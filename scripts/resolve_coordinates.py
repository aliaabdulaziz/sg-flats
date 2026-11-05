"""Corroborate HDB address labels with NUS footprints and official HDB polygons.

No fuzzy address matching or block-number-only acceptance. Full coordinates stay local.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import pandas as pd
from pyproj import Transformer
from shapely.geometry import MultiPoint, shape
from shapely.ops import transform
from download_phase0 import ROOT, fetch

NUS_COMMIT = '4a87d9c2811ea43969d9788a5cb4c9a55a977ad9'
NUS_URL = f'https://raw.githubusercontent.com/ualsg/hdb3d-data/{NUS_COMMIT}/hdb.json'
MIN_IOU = 0.50
MIN_ANCHORS = 3


def norm(value):
    return ' '.join(str(value).upper().strip().split())


def indices(value):
    if isinstance(value, int):
        yield value
    elif isinstance(value, list):
        for part in value:
            yield from indices(part)


def main():
    raw = ROOT / 'data/raw'
    path = raw / 'nus_hdb3d.json'
    if not path.exists():
        path.write_bytes(fetch(NUS_URL))
    nus = json.loads(path.read_text())
    assert not nus.get('transform'), 'CityJSON transform requires explicit handling'
    vertices = nus['vertices']
    to_xy = Transformer.from_crs(4326, 3414, always_xy=True).transform
    to_lonlat = Transformer.from_crs(3414, 4326, always_xy=True).transform
    features = json.loads((raw / 'buildings.geojson').read_text())['features']
    by_block = defaultdict(list)
    official = []
    invalid = []
    for f in features:
        p = f['properties']
        geom = transform(to_xy, shape(f['geometry']))
        if not geom.is_valid or geom.is_empty or geom.area <= 0:
            invalid.append(p['OBJECTID'])
            continue
        rec = {'objectid': p['OBJECTID'], 'block': norm(p['BLK_NO']),
               'street_code': p['ST_COD'], 'postcode': str(p['POSTAL_COD']).zfill(6),
               'geom': geom}
        official.append(rec)
        by_block[rec['block']].append(rec)
    seeds = []
    rejected = defaultdict(int)
    for objectid, obj in nus['CityObjects'].items():
        a = obj.get('attributes', {})
        block, street = norm(a.get('hdb_blk_no', '')), norm(a.get('hdb_street', ''))
        if not block or not street:
            rejected['missing_address'] += 1
            continue
        ids = set(i for geometry in obj.get('geometry', []) for i in indices(geometry['boundaries']))
        hull = MultiPoint([(vertices[i][0], vertices[i][1]) for i in ids]).convex_hull
        if not hull.is_valid or hull.area <= 0:
            rejected['invalid_nus_footprint'] += 1
            continue
        matches = []
        for candidate in by_block[block]:
            geom = candidate['geom']
            if not hull.intersects(geom):
                continue
            iou = hull.intersection(geom).area / hull.union(geom).area
            if iou >= MIN_IOU:
                matches.append((candidate, iou))
        if len(matches) != 1:
            rejected['no_unique_overlap_match'] += 1
            continue
        candidate, iou = matches[0]
        point = candidate['geom'].representative_point()
        seeds.append({'address_key': block+'|'+street, 'block': block, 'street': street,
                      'objectid': candidate['objectid'], 'street_code': candidate['street_code'],
                      'iou': iou, 'nus_centroid_offset_m': hull.centroid.distance(candidate['geom'].centroid),
                      'nus_objectid': objectid})
    seeds = pd.DataFrame(seeds)
    # An official object and an address must each have only one accepted association.
    bad_addresses = set(seeds.groupby('address_key').objectid.nunique().loc[lambda x: x > 1].index)
    bad_objects = set(seeds.groupby('objectid').address_key.nunique().loc[lambda x: x > 1].index)
    seeds = seeds.loc[~seeds.address_key.isin(bad_addresses) & ~seeds.objectid.isin(bad_objects)].sort_values('iou', ascending=False).drop_duplicates('address_key')

    def crosswalk(frame):
        result = {}
        for code, group in frame.groupby('street_code'):
            if group.street.nunique() == 1 and group.block.nunique() >= MIN_ANCHORS:
                result[code] = group.street.iloc[0]
        return result

    # Address-disjoint holdout: use only training anchors to infer street names.
    test = seeds.address_key.map(lambda x: int(hashlib.sha256(x.encode()).hexdigest()[:8],16) % 5 == 0)
    train_map = crosswalk(seeds.loc[~test])
    holdout = seeds.loc[test].copy()
    holdout['inferred_street'] = holdout.street_code.map(train_map)
    holdout_covered = holdout.inferred_street.notna()
    report = ROOT / 'reports/phase0/coordinates'
    report.mkdir(parents=True,exist_ok=True)
    holdout.loc[holdout_covered & holdout.inferred_street.ne(holdout.street)].to_csv(report/'holdout-disagreements.csv',index=False)
    conflicts = set(seeds.groupby('street_code').street.nunique().loc[lambda x:x>1].index)
    seeds.loc[seeds.street_code.isin(conflicts)].to_csv(report/'street-code-conflicts.csv',index=False)
    # Contradictory street-code labels are quarantined, including direct matches.
    usable_seeds = seeds.loc[~seeds.street_code.isin(conflicts)]
    inferred = crosswalk(usable_seeds)
    candidates = defaultdict(list)
    by_id = {x['objectid']: x for x in official}
    for record in official:
        street = inferred.get(record['street_code'])
        if street:
            candidates[record['block']+'|'+street].append(record)
    direct = usable_seeds.set_index('address_key').to_dict('index')
    resale = pd.read_csv(raw / 'resale.csv', dtype=str)
    resale['address_key'] = resale.block.map(norm)+'|'+resale.street_name.map(norm)
    addresses = resale.groupby(['address_key','block','street_name','town'],as_index=False).size().rename(columns={'size':'transactions'})
    output = []
    for row in addresses.to_dict('records'):
        key = row['address_key']
        source = None
        record = None
        if key in direct:
            record = by_id[direct[key]['objectid']]
            source = 'footprint_corroborated'
        elif len(candidates[key]) == 1 and key not in bad_addresses:
            record = candidates[key][0]
            source = 'street_crosswalk_inferred'
        if record is not None:
            point = record['geom'].representative_point()
            lon, lat = to_lonlat(point.x, point.y)
            row.update({'match_status': source,'objectid': record['objectid'],
                        'postcode': record['postcode'],'street_code': record['street_code'],
                        'longitude':lon,'latitude':lat,'x_svy21':point.x,'y_svy21':point.y})
        else:
            row['match_status'] = 'unresolved'
        output.append(row)
    result = pd.DataFrame(output)
    assert result.address_key.is_unique
    assert result.transactions.sum() == len(resale)
    accepted = result.match_status.ne('unresolved')
    assert result.loc[accepted,'latitude'].between(1.15,1.50).all()
    assert result.loc[accepted,'longitude'].between(103.55,104.10).all()
    assert not result.loc[accepted,'objectid'].duplicated().any(), 'Two addresses resolved to same building'
    processed = ROOT / 'data/processed'
    processed.mkdir(parents=True,exist_ok=True)
    result.to_csv(processed / 'block_coordinates.csv', index=False)
    report = ROOT / 'reports/phase0/coordinates'
    report.mkdir(parents=True,exist_ok=True)
    result.loc[~accepted,['block','street_name','town','transactions','match_status']].to_csv(report/'unresolved-addresses.csv',index=False)
    groups = result.groupby(['town','match_status'],as_index=False).agg(addresses=('address_key','size'),transactions=('transactions','sum'))
    groups.to_csv(report/'coverage-by-town.csv',index=False)
    # Evidence sample, avoiding an unreviewed bulk address database in the repository.
    seeds.sort_values('address_key').groupby(seeds.street_code,sort=True).head(1).head(40).to_csv(report/'footprint-evidence-sample.csv',index=False)
    pd.DataFrame([{'street_code':k,'street':v,'anchor_blocks':int(seeds.loc[seeds.street_code.eq(k),'block'].nunique())} for k,v in sorted(inferred.items())]).to_csv(report/'street-crosswalk-evidence.csv',index=False)
    summary = {'method':'NUS labelled footprint corroboration plus conservative street-code inference',
               'minimum_iou':MIN_IOU,'minimum_crosswalk_anchor_blocks':MIN_ANCHORS,
               'official_valid_polygons':len(official),'official_invalid_polygons':len(invalid),
               'nus_objects':len(nus['CityObjects']),'rejected_nus_objects':dict(rejected),
               'conflicting_address_keys':len(bad_addresses),'conflicting_official_objects':len(bad_objects),
               'candidate_seed_addresses':len(seeds),'quarantined_street_codes':len(conflicts),'accepted_seed_addresses':len(usable_seeds),'street_codes_with_crosswalk':len(inferred),
               'address_counts':result.match_status.value_counts().to_dict(),
               'transaction_counts':result.groupby('match_status').transactions.sum().to_dict(),
               'address_coverage_pct':float(accepted.mean()*100),
               'transaction_coverage_pct':float(result.loc[accepted,'transactions'].sum()/len(resale)*100),
               'holdout':{'addresses':len(holdout),'covered':int(holdout_covered.sum()),
                          'correct_street_names':int(holdout.loc[holdout_covered,'inferred_street'].eq(holdout.loc[holdout_covered,'street']).sum())},
               'iou_quantiles':seeds.iou.quantile([0,.1,.5,.9,1]).to_dict(),
               'source':{'nus_url':NUS_URL,'nus_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         'official_sha256':hashlib.sha256((raw/'buildings.geojson').read_bytes()).hexdigest()},
               'limitations':['Not independent survey ground truth; NUS has known geocoding errors and shares HDB lineage.',
                              'Crosswalk-inferred matches are lower assurance than direct footprint corroboration.',
                              'Current geometry is not proof of historical building/address continuity.',
                              'Missing and conflicting addresses are not assigned approximate coordinates.']}
    (report/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    main()
