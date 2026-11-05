"""Resolve remaining addresses and audit a reproducible, town-stratified sample.

Credentials are read locally; only minimum successful address results are cached.
"""
import json
import argparse
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform
from download_phase0 import ROOT
from resolve_coordinates import norm


def token():
    value = os.getenv('ONEMAP_ACCESS_TOKEN')
    if not value and (ROOT/'.env').exists():
        for line in (ROOT/'.env').read_text().splitlines():
            key, sep, candidate = line.strip().partition('=')
            if sep and key == 'ONEMAP_ACCESS_TOKEN':
                value = candidate.strip().strip('\"').strip("'")
    if not value:
        raise SystemExit('Set ONEMAP_ACCESS_TOKEN locally before running this script.')
    return value


def canonical(street):
    words = {'RD':'ROAD','ST':'STREET','AVE':'AVENUE','DR':'DRIVE','NTH':'NORTH',
             'STH':'SOUTH','BT':'BUKIT','JLN':'JALAN','CRES':'CRESCENT','TER':'TERRACE',
             'CL':'CLOSE','UPP':'UPPER','PL':'PLACE','HTS':'HEIGHTS','PK':'PARK',
             'CTR':'CENTRAL','CTRL':'CENTRAL','GDNS':'GARDENS','KG':'KAMPONG','TG':'TANJONG','LOR':'LORONG',"C'WEALTH":'COMMONWEALTH'}
    return ' '.join(words.get(word,word) for word in norm(street).replace('ST.','SAINT').split()).replace("'",'').replace('’','')


def query(block, street, access_token):
    rows = []
    for page in range(1,6):
        params = urllib.parse.urlencode({'searchVal':block+' '+street,'returnGeom':'Y',
                                         'getAddrDetails':'Y','pageNum':page})
        request = urllib.request.Request('https://www.onemap.gov.sg/api/common/elastic/search?'+params,
                                          headers={'Authorization':access_token})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request,timeout=30) as response:
                    data = json.load(response)
                break
            except urllib.error.HTTPError as error:
                if error.code in (401,403):
                    raise SystemExit('OneMap authentication failed; no token value was logged.')
                if error.code != 429 or attempt == 3:
                    raise RuntimeError('OneMap request failed: HTTP '+str(error.code)) from None
                time.sleep(15*(attempt+1))
        if data.get('error'):
            raise RuntimeError('OneMap returned an error; check credentials or service status.')
        rows.extend(data.get('results',[]))
        time.sleep(0.35)
        if page >= int(data.get('totalNumPages',0)):
            break
    exact = {}
    address_rows = []
    for r in rows:
        if norm(r.get('BLK_NO','')) == norm(block) and canonical(r.get('ROAD_NAME','')) == canonical(street):
            address_rows.append(r)
            postal = str(r.get('POSTAL',''))
            if len(postal) == 6 and postal.isdigit():
                key = (postal,float(r['LONGITUDE']),float(r['LATITUDE']))
                exact[key] = {'postcode':postal,'longitude':key[1],'latitude':key[2],
                              'block':r['BLK_NO'],'street':r['ROAD_NAME']}
    if len(exact)>1 and len({key[0] for key in exact})>1:
        features=json.loads((ROOT/'data/raw/buildings.geojson').read_text())['features']
        to_xy=Transformer.from_crs(4326,3414,always_xy=True).transform
        eligible=[]
        for r in exact.values():
            polygons=[f for f in features if str(f['properties']['POSTAL_COD'])==r['postcode'] and norm(f['properties']['BLK_NO'])==norm(block)]
            if len(polygons)==1:
                g=transform(to_xy,shape(polygons[0]['geometry']))
                if g.is_valid and Point(*to_xy(r['longitude'],r['latitude'])).distance(g)<=100:eligible.append(r)
        if len(eligible)==1:
            return {'status':'exact',**eligible[0],'coordinate_basis':'onemap_point_hdb_polygon_disambiguated'}
    if not exact and address_rows:
        features=json.loads((ROOT/'data/raw/buildings.geojson').read_text())['features']
        to_xy=Transformer.from_crs(4326,3414,always_xy=True).transform
        to_lonlat=Transformer.from_crs(3414,4326,always_xy=True).transform
        candidates={}
        for f in features:
            p=f['properties']
            if norm(p['BLK_NO'])!=norm(block):continue
            g=transform(to_xy,shape(f['geometry']))
            if not g.is_valid:continue
            if any(Point(*to_xy(float(r['LONGITUDE']),float(r['LATITUDE']))).distance(g)<=20 for r in address_rows):
                candidates[str(p['POSTAL_COD'])]=(p,g)
        if len(candidates)==1:
            postcode,(p,g)=next(iter(candidates.items()))
            lon,lat=to_lonlat(g.representative_point().x,g.representative_point().y)
            return {'status':'exact','postcode':postcode,'longitude':lon,'latitude':lat,
                    'block':block,'street':street,'coordinate_basis':'exact_address_spatial_hdb_polygon_postcode'}
    if len(exact)>1 and len({key[0] for key in exact})==1:
        postcode=next(iter(exact))[0]
        features=json.loads((ROOT/'data/raw/buildings.geojson').read_text())['features']
        polygons=[f for f in features if str(f['properties']['POSTAL_COD'])==postcode and norm(f['properties']['BLK_NO'])==norm(block)]
        if len(polygons)==1:
            to_xy=Transformer.from_crs(4326,3414,always_xy=True).transform
            to_lonlat=Transformer.from_crs(3414,4326,always_xy=True).transform
            polygon=transform(to_xy,shape(polygons[0]['geometry']))
            if polygon.is_valid and all(Point(*to_xy(r['longitude'],r['latitude'])).distance(polygon)<=100 for r in exact.values()):
                lon,lat=to_lonlat(polygon.representative_point().x,polygon.representative_point().y)
                return {'status':'exact','postcode':postcode,'longitude':lon,'latitude':lat,
                        'block':block,'street':street,'coordinate_basis':'official_polygon_for_unique_postcode'}
    if len(exact) != 1:
        return {'status':'unresolved' if not exact else 'ambiguous','exact_results':len(exact)}
    return {'status':'exact',**next(iter(exact.values()))}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--retry-unresolved',action='store_true')
    args=parser.parse_args()
    access_token = token()
    coordinates = pd.read_csv(ROOT/'data/processed/block_coordinates.csv',dtype={'block':str,'postcode':str,'objectid':str})
    # Six matched addresses per town: three from each confidence tier where available.
    sampled = []
    for (town,status),g in coordinates.loc[coordinates.match_status.ne('unresolved')].groupby(['town','match_status']):
        sampled.append(g.sort_values('address_key').sample(n=min(3,len(g)),random_state=2026))
    validation = pd.concat(sampled).copy()
    validation['purpose'] = 'stratified_validation'
    unresolved = coordinates.loc[coordinates.match_status.eq('unresolved')].copy()
    unresolved['purpose'] = 'resolve_unmatched'
    anchors = coordinates.loc[coordinates.match_status.ne('unresolved')].sort_values('address_key').drop_duplicates('street_code').copy()
    anchors['purpose'] = 'street_code_validation'
    queue = pd.concat([unresolved,validation,anchors]).drop_duplicates('address_key')
    cache_path = ROOT/'data/interim/onemap-validation.json'
    cache_path.parent.mkdir(parents=True,exist_ok=True)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    for i,row in enumerate(queue.to_dict('records'),1):
        key = row['address_key']
        if key not in cache or (args.retry_unresolved and cache[key]['status']!='exact'):
            cache[key] = query(row['block'],row['street_name'],access_token)
            cache_path.write_text(json.dumps(cache,indent=2)+'\n')
        if i%25==0 or i==len(queue):
            print(f'Address checks complete: {i}/{len(queue)}',flush=True)
    to_xy = Transformer.from_crs(4326,3414,always_xy=True).transform
    polygons = {}
    for f in json.loads((ROOT/'data/raw/buildings.geojson').read_text())['features']:
        p=f['properties'];g=transform(to_xy,shape(f['geometry']))
        if g.is_valid and not g.is_empty:polygons[str(p['POSTAL_COD'])]=(p,g)
    evidence=[]
    for row in queue.to_dict('records'):
        r=cache[row['address_key']]
        e={k:row[k] for k in ['address_key','block','street_name','town','purpose','match_status','street_code','postcode']}
        e['onemap_status']=r['status']
        e['coordinate_basis']=r.get('coordinate_basis','onemap_point')
        if r['status']=='exact':
            point=Point(*to_xy(r['longitude'],r['latitude']))
            e.update({'onemap_postcode':r['postcode'],'longitude':r['longitude'],'latitude':r['latitude']})
            if row['match_status']!='unresolved':
                old=Point(*to_xy(float(row['longitude']),float(row['latitude'])))
                e['previous_point_distance_m']=old.distance(point)
                e['postcode_agrees']=row['postcode']==r['postcode']
            if r['postcode'] in polygons:
                p,g=polygons[r['postcode']]
                e['official_polygon_distance_m']=point.distance(g)
                e['official_block_agrees']=norm(p['BLK_NO'])==norm(row['block'])
                e['official_objectid']=p['OBJECTID']
                e['official_street_code']=p['ST_COD']
            else:
                e['official_polygon_distance_m']=None
        evidence.append(e)
    evidence=pd.DataFrame(evidence)
    # Replace queried rows with official geocodes. Distant polygon disagreements are quarantined.
    final=coordinates.copy()
    code_disagreements=set(evidence.loc[evidence.purpose.ne('resolve_unmatched') & evidence.onemap_status.eq('exact') & evidence.postcode_agrees.eq(False),'street_code'].dropna())
    final.loc[final.street_code.isin(code_disagreements),'match_status']='review_street_code_disagreement'
    for e in evidence.to_dict('records'):
        if e['onemap_status']!='exact':continue
        distance=e.get('official_polygon_distance_m')
        known_polygon=pd.notna(distance)
        if known_polygon and (distance>100 or e.get('official_block_agrees') is False):
            final.loc[final.address_key.eq(e['address_key']),'match_status']='review_onemap_polygon_conflict'
            continue
        mask=final.address_key.eq(e['address_key'])
        if known_polygon:
            final.loc[mask,['objectid','street_code']]=[str(e['official_objectid']),e['official_street_code']]
        x,y=to_xy(e['longitude'],e['latitude'])
        final.loc[mask,['longitude','latitude','x_svy21','y_svy21','postcode','match_status']]=[
            e['longitude'],e['latitude'],x,y,e['onemap_postcode'],
            'onemap_exact_polygon_corroborated' if known_polygon else 'onemap_exact_no_polygon']
    assert final.address_key.is_unique
    assert final.transactions.sum()==coordinates.transactions.sum()
    accepted=~(final.match_status.eq('unresolved')|final.match_status.str.startswith('review'))
    assert final.loc[accepted,'latitude'].between(1.15,1.50).all()
    assert final.loc[accepted,'longitude'].between(103.55,104.10).all()
    assert final.loc[accepted,'postcode'].str.fullmatch(r'\d{6}').all()
    final.to_csv(ROOT/'data/processed/block_coordinates_validated.csv',index=False)
    report=ROOT/'reports/phase0/coordinates'
    evidence.to_csv(ROOT/'data/processed/onemap-validation-full.csv',index=False)
    evidence.loc[evidence.purpose.eq('stratified_validation') | evidence.coordinate_basis.ne('onemap_point') | evidence.onemap_status.ne('exact')].to_csv(report/'onemap-validation.csv',index=False)
    final.groupby(['town','match_status'],as_index=False).agg(addresses=('address_key','size'),transactions=('transactions','sum')).to_csv(report/'coverage-by-town.csv',index=False)
    final.loc[final.match_status.eq('unresolved')|final.match_status.str.startswith('review'),
              ['address_key','town','transactions','match_status']].to_csv(report/'remaining-review.csv',index=False)
    v=evidence.loc[evidence.purpose.eq('stratified_validation')]
    summary={'queried_addresses':len(evidence),'validation_sample_addresses':len(v),
             'validation_exact_results':int(v.onemap_status.eq('exact').sum()),
             'validation_postcode_agreements':int(v.postcode_agrees.eq(True).sum()),
             'validation_previous_distance_m':v.loc[v.coordinate_basis.eq('onemap_point'),'previous_point_distance_m'].describe().to_dict(),
             'validation_coordinate_basis_counts':v.coordinate_basis.value_counts().to_dict(),
             'onemap_result_statuses':evidence.onemap_status.value_counts().to_dict(),
             'accepted_coordinate_basis_counts':evidence.loc[evidence.onemap_status.eq('exact'),'coordinate_basis'].value_counts().to_dict(),
             'final_address_statuses':final.match_status.value_counts().to_dict(),
             'street_code_anchors_requested':len(anchors),
             'street_codes_with_postcode_disagreement':sorted(code_disagreements),
             'street_codes_with_exact_checked_addresses':int(evidence.loc[evidence.onemap_status.eq('exact'),'street_code'].nunique()),
             'final_transaction_statuses':final.groupby('match_status').transactions.sum().to_dict(),
             'remaining_review_addresses':int((final.match_status.eq('unresolved')|final.match_status.str.startswith('review')).sum()),
             'notes':['Stratified validation is an address sample, not a guarantee for every unqueried block.',
                      'Point-to-polygon distances above 100m require review; threshold is a project rule, not an official accuracy specification.',
                      'Official geocodes are current address results; they do not establish historical continuity.']}
    (report/'onemap-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':main()
