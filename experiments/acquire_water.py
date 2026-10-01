"""Current official occurrence percentages, frozen before their pixels."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import urllib.request

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.acquisition/water_20261002'; ASSETS=ROOT/'integration/water_assets_20261002.json'
OUT=ROOT/'data/water_20261002'
BASE='https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/'
SITES=('london','chicago','hanoi','buenos_aires','bangkok','rio_de_janeiro','toronto','nairobi')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def freeze():
    if ASSETS.exists(): raise ValueError('Refuse overwrite water assets')
    listing=json.loads((CACHE/'official_file_list.json').read_text())
    cities={a['site']:a for a in json.loads((ROOT/'integration/expanded_assets_20261002.json').read_text())['sites']}
    rows=[]
    for name in SITES:
        a=cities[name]; left=math.floor(a['longitude']/10)*10; top=math.ceil(a['latitude']/10)*10
        filename=f'occurrence_{abs(left)}'+('E' if left>=0 else 'W')+f'_{abs(top)}'+('N' if top>=0 else 'S')+'_v1_5_2024.tif'
        record=next(r for r in listing if r['name'].endswith(filename))
        row=math.floor((top-a['latitude'])*4000); col=math.floor((a['longitude']-left)*4000)
        if not 256<=row<=39744 or not 256<=col<=39744: raise ValueError('Window boundary')
        rows.append(dict(site=name,latitude=a['latitude'],longitude=a['longitude'],geonameid=a['geonameid'],
            official_record=record,url=BASE+record['name'],filename=filename,left=left,top=top,
            window=dict(row_off=row-256,col_off=col-256,height=512,width=512)))
    save(ASSETS,dict(status='FROZEN_BEFORE_WATER_PIXELS',sites=rows,product='JRC Global Surface Water occurrence v1.5 1984–2024',
        official_listing_sha256=sha(CACHE/'official_file_list.json'),official_listing_url=BASE+'?format=json',
        cap=100,nodata=255,zero_semantics='observed not water',units='percentage-point sums',
        native_grid='EPSG:4326; 0.00025 degree; nominal 30 m',size=512,
        budgets=[5,10,25,50,100,250,500,1000],step_rule='min(cap,max(1,epsilon//5))',
        no_value_dependent_selection=True,credit='EC JRC/Google; Pekel et al., Nature 540, 418–422 (2016)',
        guide='https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf'))


def download(a):
    target=CACHE/a['filename']; partial=target.with_suffix('.tif.partial')
    if target.exists() or partial.exists(): raise ValueError('No archive overwrite')
    if shutil.disk_usage(ROOT).free < 6*(1<<30): raise OSError('Disk reserve')
    req=urllib.request.Request(a['url'],headers={'User-Agent':'DCC-native-window-research/2'})
    with urllib.request.urlopen(req,timeout=180) as response,partial.open('xb') as f:
        headers=dict(response.headers.items()); count=0
        for block in iter(lambda:response.read(1<<20),b''):
            count+=len(block)
            if count>a['official_record']['bytes']: raise ValueError('Official size exceeded')
            f.write(block)
        if response.status!=200 or count!=a['official_record']['bytes']: raise ValueError('Official file size')
    partial.rename(target)
    save(CACHE/(a['site']+'-http.json'),dict(url=a['url'],headers=headers,bytes=count,sha256=sha(target)))
    return a,target


def extract(a,path):
    import rasterio
    from rasterio.windows import Window
    row=dict(site=a['site'],status='FAIL',url=a['url'],tile_sha256=sha(path))
    try:
        with rasterio.open(path) as ds:
            if (ds.count!=1 or ds.dtypes!=('uint8',) or ds.nodata not in (None,255) or ds.shape!=(40000,40000)
                or ds.crs.to_epsg()!=4326
                or not np.allclose(list(ds.transform)[:6],[.00025,0,a['left'],0,-.00025,a['top']],rtol=0,atol=1e-12)):
                raise ValueError('Official raster header')
            win=Window(**a['window']); raw=ds.read(1,window=win); mask=raw==255
            if raw.shape!=(512,512) or np.any(raw[~mask]>100): raise ValueError('Occurrence range')
            source=OUT/(a['site']+'.npz')
            if source.exists(): raise ValueError('Refuse overwrite water source')
            np.savez_compressed(source,raw=raw,mask=mask)
            row.update(status='PASS_NATIVE_OCCURRENCE',source=str(source.relative_to(ROOT)),source_sha256=sha(source),
                missing=int(mask.sum()),valid=int((~mask).sum()),native_nodata_tag=ds.nodata,
                missing_semantics='255 from official product guide; zero is not water',
                raw_uint8_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),
                geo=dict(crs=ds.crs.to_wkt(),affine=list(ds.window_transform(win))[:6],
                         units='percentage points',product='JRC GSW occurrence v1.5 1984–2024',resampling=False))
    except Exception as e: row['error']=str(e)
    return row


def repair_nodata_tag():
    target=OUT/'manifest_v2.json'
    if target.exists(): raise ValueError('Refuse overwrite water amendment')
    assets=json.loads(ASSETS.read_text()); rows=[]
    for a in assets['sites']:
        row=extract(a,CACHE/a['filename']); rows.append(row)
        print(a['site'],row['status'],row.get('error'),flush=True)
    save(target,dict(status='PASS_EIGHT_OCCURRENCE_WINDOWS' if all(r['status']=='PASS_NATIVE_OCCURRENCE' for r in rows) else 'PARTIAL',
        rows=rows,assets_sha256=sha(ASSETS),previous_manifest_sha256=sha(OUT/'manifest.json'),
        amendment='Official files omit the TIFF NoData tag; the official guide defines the sentinel 255',
        geographic_footprints_changed=False,pixels_resampled=False,gpu_used=False))


def run():
    import rasterio
    from rasterio.windows import Window
    import subprocess
    if OUT.exists(): raise ValueError('Fresh scientific water output')
    head=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    if subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True): raise ValueError('Clean protocol tree')
    if subprocess.check_output(['git','-C',str(ROOT),'ls-remote','origin','refs/heads/main'],text=True).split()[0]!=head:
        raise ValueError('Pushed water protocol')
    OUT.mkdir(); rows=[]; assets=json.loads(ASSETS.read_text())
    with ThreadPoolExecutor(max_workers=3) as pool:
        for a,path in pool.map(download,assets['sites']):
            row=extract(a,path)
            rows.append(row); save(OUT/'manifest.json',dict(status='RUNNING',launch_commit=head,rows=rows,assets_sha256=sha(ASSETS)))
            print(a['site'],row['status'],row.get('error'),flush=True)
    save(OUT/'manifest.json',dict(status='PASS_EIGHT_OCCURRENCE_WINDOWS' if all(r['status']=='PASS_NATIVE_OCCURRENCE' for r in rows) else 'PARTIAL',
        launch_commit=head,rows=rows,assets_sha256=sha(ASSETS),pixels_resampled=False,gpu_used=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['freeze','run','repair-nodata']); a=p.parse_args()
    if a.action=='freeze': freeze()
    elif a.action=='run': run()
    else: repair_nodata_tag()
