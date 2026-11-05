"""Build a sourced, conservative MRT service-date register and audit geometry joins."""
import io
import json
import re
import zipfile
import pandas as pd
import shapefile
from shapely.geometry import shape
from shapely.ops import unary_union
from pyproj import Transformer
from download_phase0 import ROOT, fetch

BASE='https://www.lta.gov.sg/content/ltagov/en/'
SOURCES={
 'legacy': 'https://www.lta.gov.sg/content/dam/ltagov/who_we_are/statistics_and_publications/statistics/pdf/Rail_Length_2024.pdf',
 'dtl':BASE+'getting_around/public_transport/rail_network/downtown_line.html',
 'tel':BASE+'upcoming_projects/rail_expansion/thomson_east_coast_line.html',
 'canberra':'https://www.lta.gov.sg/content/dam/ltagov/who_we_are/statistics_and_publications/report/pdf/LTA_AR1920.pdf',
 'tuas':'https://www.mot.gov.sg/news-resources/newsroom/speech-by-second-minister-ng-chee-meng-at-tuas-west-extension-opening-ceremony/',
 'punggol':BASE+'newsroom/2024/12/news-releases/punggol_coast_station_welcomes_commuters.html',
 'hume':BASE+'newsroom/2025/1/news-releases/hume_station_to_open.html',
 'ccl6':BASE+'upcoming_projects/rail_expansion/circle_line_6.html',
 'future':BASE+'newsroom/2026/11/news-releases/tel5-dtl3e-passenger-service-26-dec-2026.html',
 'tecklee':BASE+'newsroom/2024/7/news-releases/Teck_Lee_LRT_station_to_start_operations.html',
 'closure':'https://www.lta.gov.sg/content/dam/ltagov/news/press/2018/20181212_BPLRT_train_timings_AnnexA.pdf',
}


def read_shape(name):
 z=zipfile.ZipFile(ROOT/'data/raw'/f'{name}.zip')
 stem=next(x[:-4] for x in z.namelist() if x.endswith('.shp'))
 return shapefile.Reader(shp=io.BytesIO(z.read(stem+'.shp')),dbf=io.BytesIO(z.read(stem+'.dbf')))


def main():
 path=ROOT/'data/raw/station_codes.zip'
 if not path.exists():
  path.write_bytes(fetch('https://datamall.lta.gov.sg/content/dam/datamall/datasets/Geospatial/Train%20Station%20Codes%20and%20Chinese%20Names.zip'))
 z=zipfile.ZipFile(path)
 codes=pd.read_excel(io.BytesIO(z.read(z.namelist()[0])))
 rows=[]
 for r in codes.to_dict('records'):
  code=r['stn_code'];prefix=re.match('[A-Z]+',code)[0];n=int(re.search(r'\d+',code)[0]) if re.search(r'\d+',code) else 0
  entry={'station_code':code,'station_name':' '.join(r['mrt_station_english'].split()),
         'line':r['mrt_line_english'],'available_from':'','date_type':'unverified',
         'history_scope':'not_approved','source_url':''}
  if prefix in ('NS','EW','NE','CC','CE','CG','DT'):
   entry.update(available_from='2017-01-01',date_type='left_censored_before_model_window',
                history_scope='MRT_service_availability_from_2017',source_url=SOURCES['legacy'])
  event=None
  if code=='NS12':event=('2019-11-02','canberra')
  elif prefix=='EW' and n>=30:event=('2017-06-18','tuas')
  elif code=='NE18':event=('2024-12-10','punggol')
  elif code=='DT4':event=('2025-02-28','hume')
  elif prefix=='DT' and 20<=n<=35:event=('2017-10-21','dtl')
  elif prefix=='TE':
   if 1<=n<=3:event=('2020-01-31','tel')
   elif 4<=n<=9:event=('2021-08-28','tel')
   elif 11<=n<=22 and n!=21:event=('2022-11-13','tel')
   elif 23<=n<=29:event=('2024-06-23','tel')
  if event:
   entry.update(available_from=event[0],date_type='passenger_service_date',
                history_scope='MRT_service_availability_from_2017',source_url=SOURCES[event[1]])
  if code=='PW2':
   entry.update(available_from='2024-08-15',date_type='passenger_service_date',
                history_scope='LRT_event_only_network_incomplete',source_url=SOURCES['tecklee'])
  rows.append(entry)
 for code,name in [('CC30','Keppel'),('CC31','Cantonment'),('CC32','Prince Edward Road')]:
  rows.append({'station_code':code,'station_name':name,'line':'Circle Line',
               'available_from':'2026-07-12','date_type':'passenger_service_date',
               'history_scope':'MRT_service_availability_from_2017','source_url':SOURCES['ccl6']})
 # Announced future dates must never become operational history before confirmation.
 for code,name in [('TE30','Bedok South'),('TE31','Sungei Bedok'),('DT36','Xilin'),('DT37','Sungei Bedok')]:
  rows.append({'station_code':code,'station_name':name,'line':'Future extension',
               'available_from':'','announced_date':'2026-12-26','date_type':'announced_future_only',
               'history_scope':'not_approved','source_url':SOURCES['future']})
 for code,name in [('TE10','Mount Pleasant'),('TE21','Marina South'),('TE22A',"Founders' Memorial")]:
  rows.append({'station_code':code,'station_name':name,'line':'Thomson-East Coast Line',
               'available_from':'','date_type':'deferred_unconfirmed',
               'history_scope':'not_approved','source_url':SOURCES['tel']})
 registry=pd.DataFrame(rows)
 assert registry.station_code.is_unique
 approved=registry.loc[registry.history_scope.eq('MRT_service_availability_from_2017')]
 assert approved.available_from.ne('').all()
 report=ROOT/'reports/phase0/transport'
 report.mkdir(parents=True,exist_ok=True)
 registry.to_csv(ROOT/'data/reference/rail-service-register.csv',index=False)
 geometries=[]
 for r in read_shape('stations').records():
  a=r.as_dict();labels=[c.strip() for c in a['STN_NAM'].split('/')]
  for label in labels:
   match=registry.loc[registry.station_code.eq(label)]
   geometries.append({'geometry_label':a['STN_NAM'],'code_candidate':label,'geometry_line':a['LIN_NAM'],
                      'matched_code':len(match)==1,'historical_scope':match.history_scope.iloc[0] if len(match)==1 else 'unclassified',
                      'station_name':match.station_name.iloc[0] if len(match)==1 else ''})
 geometry=pd.DataFrame(geometries)
 geometry.to_csv(report/'station-geometry-classification.csv',index=False)
 approved_codes=set(approved.station_code)
 missing=sorted(approved_codes-set(geometry.loc[geometry.matched_code,'code_candidate']))
 # Match missing interchange codes by the official shared physical-station name.
 physical_polygons={}
 invalid_geometries=0
 for sr in read_shape('stations').iterShapeRecords():
  record=sr.record.as_dict()
  geom=shape(sr.shape.__geo_interface__)
  if not geom.is_valid or geom.is_empty:
   invalid_geometries+=1
   continue
  for label in record['STN_NAM'].split('/'):
   match=registry.loc[registry.station_code.eq(label.strip())]
   if len(match)==1 and match.history_scope.iloc[0]=='MRT_service_availability_from_2017':
    key=match.station_name.iloc[0].upper()
    physical_polygons.setdefault(key,[]).append((match.available_from.iloc[0],geom))
 to_lonlat=Transformer.from_crs(3414,4326,always_xy=True).transform
 points=[]
 for r in approved.to_dict('records'):
  dated_polygons=physical_polygons.get(r['station_name'].upper(),[])
  if not dated_polygons:continue
  first_date=min(date for date,geom in dated_polygons)
  polygons=[geom for date,geom in dated_polygons if date==first_date]
  point=unary_union(polygons).representative_point()
  lon,lat=to_lonlat(point.x,point.y)
  points.append({'station_code':r['station_code'],'station_name':r['station_name'],
                 'x_svy21':point.x,'y_svy21':point.y,'longitude':lon,'latitude':lat,
                 'geometry_method':'shared_physical_station_proxy' if r['station_code'] in missing else 'station_polygon_proxy'})
 point_table=pd.DataFrame(points)
 remaining=sorted(approved_codes-set(point_table.station_code))
 point_table.to_csv(ROOT/'data/processed/mrt_station_proxies.csv',index=False)
 point_table.loc[point_table.geometry_method.eq('shared_physical_station_proxy')].to_csv(report/'interchange-geometry-resolution.csv',index=False)
 # Opening months are mixed because transactions identify month only. Conservative use begins next month.
 approved=approved.copy()
 approved['first_full_service_month']=(pd.to_datetime(approved.available_from).dt.to_period('M')+1).astype(str)
 approved.loc[approved.date_type.eq('left_censored_before_model_window'),'first_full_service_month']='2017-01'
 approved[['station_code','station_name','available_from','first_full_service_month','date_type']].to_csv(report/'monthly-availability-policy.csv',index=False)
 # Real regression cases: service is not retrospectively assigned to earlier transaction months.
 cases=[('NS12','2019-10',False),('NS12','2019-11',False),('NS12','2019-12',True),
        ('DT4','2025-01',False),('DT4','2025-02',False),('DT4','2025-03',True),
        ('NE18','2024-11',False),('NE18','2025-01',True),('CC30','2026-06',False),('CC30','2026-08',True)]
 for code,month,expected in cases:
  threshold=approved.loc[approved.station_code.eq(code),'first_full_service_month'].iloc[0]
  assert (month>=threshold)==expected,(code,month)
 summary={'station_code_rows':len(codes),'registry_rows':len(registry),
          'approved_mrt_service_code_rows':len(approved),
          'approved_codes_missing_exact_polygon_label':missing,
          'remaining_codes_without_station_proxy':remaining,'invalid_station_geometries_excluded':invalid_geometries,
          'station_proxy_rows':len(point_table),'physical_station_names':int(point_table.station_name.nunique()),
          'geometry_classification':geometry.historical_scope.value_counts().to_dict(),
          'boundary_regression_cases_passed':len(cases),
          'historical_decision':{
           'mrt_service_dates':'supported for registered service-code set from 2017; opening month is excluded conservatively',
           'mrt_distance_features':'conditional: service dates and physical-station proxies resolved for registered MRT set; current footprint stability must be an explicit modelling assumption, not an exit-distance claim',
           'lrt':'not approved as a complete historical network; Teck Lee event documented separately',
           'station_exit_distance':'current snapshot only; exit-specific opening history not established',
           'bus_stop_or_route_features':'current snapshot only; historical additions, removals and relocations not established',
           'current_routing':'current planning only, not historical commute reconstruction'},
          'sources':SOURCES}
 (report/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
