"""Refresh official snapshots; raw request/response evidence stays separate."""
import argparse, concurrent.futures, datetime, hashlib, json, pathlib, subprocess, time
import requests
ROOT = pathlib.Path(__file__).resolve().parents[1]
API = 'https://api.usaspending.gov/api/v2/search/spending_by_geography/'
TYPES = {'contracts':['A','B','C','D'], 'grants':['02','03','04','05']}

def fetch(year, kind, force=False):
    raw = ROOT / f'data/raw/usaspending-{year}-{kind}.json'
    body = {'scope':'place_of_performance', 'geo_layer':'district', 'spending_level':'transactions', 'filters':{'time_period':[{'start_date':f'{year-1}-10-01','end_date':f'{year}-09-30'}], 'award_type_codes':TYPES[kind]}}
    if force or not raw.exists():
        for attempt in range(3):
            try:
                response=requests.post(API,json=body,timeout=120);response.raise_for_status()
                result=response.json()
                assert isinstance(result.get('results'),list)
                raw.write_text(json.dumps({'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'endpoint':API,'request':body,'response':result},indent=2))
                break
            except Exception:
                if attempt==2: raise
                time.sleep(2)
    envelope=json.loads(raw.read_text())
    return year,kind,envelope

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--force',action='store_true');args=parser.parse_args()
    entries={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(fetch,y,k,args.force) for y in range(2022,2027) for k in TYPES]
        for future in concurrent.futures.as_completed(futures):
            year,kind,env=future.result();entries[f'{year}-{kind}']=env
            print(year,kind,len(env['response']['results']),flush=True)
    geometry=json.loads((ROOT/'dist/data/districts.geojson').read_text())
    codes={f['properties']['GEOID'] for f in geometry['features']}
    years={}
    for year in range(2022,2027):
        rows={};unmapped={}
        for kind in TYPES:
            env=entries[f'{year}-{kind}'];outside=[]
            for item in env['response']['results']:
                code=item['shape_code']
                if code not in codes:
                    outside.append(item);continue
                row=rows.setdefault(code,{'id':code,'name':item['display_name'],'population':item['population'],'contracts':None,'grants':None})
                row[kind]=item['aggregated_amount']
            unmapped[kind]=outside
        years[str(year)]={'start':f'{year-1}-10-01','end':f'{year}-09-30','districts':list(rows.values()),'unmapped':unmapped}
    output={'source':API,'fetched_at':max(e['fetched_at'] for e in entries.values()),'boundary_source':'https://www2.census.gov/geo/tiger/GENZ2025/shp/cb_2025_us_cd119_500k.zip','boundary_congress':119,'award_type_codes':TYPES,'years':years}
    (ROOT/'dist/data/spending.json').write_text(json.dumps(output,separators=(',',':')))
    print('Wrote spending.json; unknown/multiple/unmatched rows retained separately.')
    from build_cycles import main as build_cycles
    build_cycles()
if __name__=='__main__':main()
