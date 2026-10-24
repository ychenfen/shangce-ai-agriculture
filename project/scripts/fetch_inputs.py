"""Download public sources once; retain unmodified bytes and a provenance ledger."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests, json, hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SITES = {'shijiazhuang': (38.04,114.51), 'zhengzhou': (34.75,113.62), 'jinan': (36.65,117.12)}
def fetch(item):
    name,url,params = item
    path=ROOT/name
    if not path.exists():
        r=requests.get(url,params=params,timeout=90); r.raise_for_status()
        path.write_bytes(r.content)
        full_url=r.url
    else:
        full_url=requests.Request('GET',url,params=params).prepare().url
    print(name, path.stat().st_size, flush=True)
    return {'file':name,'url':full_url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'retrieved_utc':datetime.now(timezone.utc).isoformat()}

if __name__=='__main__':
    jobs=[]
    for site,(lat,lon) in SITES.items():
        jobs.append((f'inputs/weather/{site}.json','https://archive-api.open-meteo.com/v1/archive',dict(latitude=lat,longitude=lon,start_date='2018-01-01',end_date='2025-12-31',daily='temperature_2m_mean,temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean,wind_speed_10m_mean,precipitation_sum,shortwave_radiation_sum,surface_pressure_mean,et0_fao_evapotranspiration',timezone='Asia/Shanghai',wind_speed_unit='ms',models='era5')))
    with ThreadPoolExecutor(max_workers=3) as pool: records=list(pool.map(fetch,jobs))
    (ROOT/'inputs/provenance.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
