"""Metadata-selected native GHS windows; no value-dependent selection."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'integration/expanded_assets_20261002.json'
CACHE = ROOT / '.acquisition/expanded_20261002'
OUT = ROOT / 'data/expanded_20261002'
CITIES = {
    'EU': [('London','GB'),('Berlin','DE'),('Warsaw','PL'),('Madrid','ES'),('Rome','IT'),
           ('Athens','GR'),('Moscow','RU'),('Istanbul','TR')],
    'NA': [('Chicago','US'),('Los Angeles','US'),('Toronto','CA'),('Montreal','CA'),
           ('Atlanta','US'),('San Francisco','US'),('Vancouver','CA'),('Mexico City','MX')],
    'SA': [('Buenos Aires','AR'),('Rio de Janeiro','BR'),('Bogota','CO'),('Lima','PE'),
           ('Santiago','CL'),('Brasilia','BR')],
    'AF': [('Johannesburg','ZA'),('Nairobi','KE'),('Casablanca','MA'),('Accra','GH'),
           ('Dakar','SN'),('Addis Ababa','ET')],
    'AS': [('Riyadh','SA'),('Tehran','IR'),('Bangkok','TH'),('Hanoi','VN'),('Manila','PH'),
           ('Seoul','KR'),('Shanghai','CN'),('Mumbai','IN')],
    'OC': [('Sydney','AU'),('Melbourne','AU'),('Auckland','NZ'),('Brisbane','AU')],
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for b in iter(lambda: stream.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def freeze():
    from pyproj import Transformer
    if ASSETS.exists():
        raise ValueError('Refuse overwrite frozen assets')
    gazetteer = CACHE / 'cities15000.zip'
    with zipfile.ZipFile(gazetteer) as z:
        records = [line.split('\t') for line in z.read('cities15000.txt').decode().splitlines()]
    transformer = Transformer.from_crs('EPSG:4326', 'ESRI:54009', always_xy=True)
    assets = []
    for region, cities in CITIES.items():
        for name, country in cities:
            matches = [r for r in records if r[8] == country and
                       name.casefold() in {r[1].casefold(), r[2].casefold(),
                                           *(n.casefold() for n in r[3].split(','))}]
            if not matches:
                raise ValueError('No GeoNames record: ' + name)
            r = max(matches, key=lambda a: (int(a[14]), -int(a[0])))
            lon, lat = float(r[5]), float(r[4])
            x, y = transformer.transform(lon, lat)
            col, row = math.floor((x + 18041000)/1e6)+1, math.floor((9000000-y)/1e6)+1
            left, top = -18041000 + (col-1)*1000000, 9000000-(row-1)*1000000
            center = [math.floor((top-y)/100), math.floor((x-left)/100)]
            clamped = [min(9488, max(512, v)) for v in center]
            tile = f'R{row}_C{col}'
            filename = f'GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_{tile}.zip'
            asset = dict(site=name.lower().replace(' ', '_'), label=name, region=region,
                country=country, geonameid=int(r[0]), geonames_ascii=r[2], population=int(r[14]),
                geonames_record_date=r[18], longitude=lon, latitude=lat,
                projected_point_m=[x,y], center_original=center, center_clamped=clamped,
                window=dict(row_off=clamped[0]-512, col_off=clamped[1]-512, height=1024, width=1024),
                tile=tile, left=left, top=top, archive=filename,
                url='https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/'
                    'GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100/V1-0/tiles/'+filename)
            # Geographic independence is checked using old pixel rectangles, not their values.
            for oldfile in (ROOT/'integration/heldout_assets_20261001.json',
                            ROOT.parent/'LinewiseROI/integration/built_area_assets_20261001.json'):
                old = json.loads(oldfile.read_text())
                for a in old['sites'] if isinstance(old, dict) else old:
                    if a.get('tile', a['archive'].split('V1_0_')[-1].split('.')[0]) != tile:
                        continue
                    w = a['window']; v = asset['window']
                    if (max(w['row_off'],v['row_off']) < min(w['row_off']+w['height'],v['row_off']+1024)
                        and max(w['col_off'],v['col_off']) < min(w['col_off']+w['width'],v['col_off']+1024)):
                        raise ValueError('Overlap with development/previous holdout')
            assets.append(asset)
    assert len(assets) == 40 and len({a['site'] for a in assets}) == 40
    save(ASSETS, dict(status='METADATA_FROZEN_BEFORE_PIXEL_DOWNLOAD', sites=assets,
        sizes=[256,512,1024], budgets=[25,50,100,250,500,1000,2500,5000],
        step_rule='max(1,epsilon//5)', band_rule='epsilon//4',
        gazetteer_url='https://download.geonames.org/export/dump/cities15000.zip',
        gazetteer_sha256=sha(gazetteer), gazetteer_license='CC-BY-4.0',
        gazetteer_credit='GeoNames', no_pixel_data_inspected=True,
        scaling_anchor='london', scaling_size=4096,
        selection='Named cities by region; highest population name/country match; metadata-only tile clamp'))


def fetch(asset):
    path = CACHE / asset['archive']
    record = CACHE / (asset['tile'] + '-http.json')
    if path.exists():
        if not record.exists() or sha(path) != json.loads(record.read_text())['sha256']:
            raise ValueError('Cached asset binding')
        return path
    partial = path.with_suffix('.zip.partial')
    if partial.exists():
        raise ValueError('Partial retained; inspect before retry')
    if shutil.disk_usage(ROOT).free < 6*(1 << 30):
        raise OSError('Leave at least 6 GiB disk free')
    request = urllib.request.Request(asset['url'], headers={'User-Agent':'DCC-native-window-research/2'})
    with urllib.request.urlopen(request, timeout=180) as response, partial.open('xb') as stream:
        headers = dict(response.headers.items()); count = 0
        for block in iter(lambda: response.read(1 << 20), b''):
            count += len(block)
            if count > 256*(1 << 20):
                raise ValueError('Archive cap')
            stream.write(block)
        if response.status != 200 or (headers.get('Content-Length') and count != int(headers['Content-Length'])):
            raise ValueError('Incomplete HTTP asset')
    partial.rename(path)
    save(record, dict(url=asset['url'], headers=headers, bytes=count, sha256=sha(path), status=200))
    return path


def acquire_site(asset):
    import rasterio
    from rasterio.windows import Window
    from pyproj import CRS
    result = dict(site=asset['site'], status='FAIL')
    try:
        archive = CACHE / asset['archive']
        with zipfile.ZipFile(archive) as z:
            entries = [n for n in z.namelist() if n.endswith('.tif')]
            if len(entries) != 1 or '..' in Path(entries[0]).parts:
                raise ValueError('Unique TIFF')
        with rasterio.open(f'/vsizip/{archive}/{entries[0]}') as dataset:
            if (dataset.shape != (10000,10000) or dataset.count != 1 or dataset.dtypes != ('uint16',)
                or dataset.nodata != 65535 or CRS(dataset.crs) != CRS.from_user_input('ESRI:54009')
                or tuple(dataset.transform)[:6] != (100.,0.,asset['left'],0.,-100.,asset['top'])):
                raise ValueError('Native asset contract')
            windows = [(1024, asset['window'])]
            if asset['site'] == 'london':
                c = [min(7952,max(2048,v)) for v in asset['center_original']]
                windows.append((4096,dict(row_off=c[0]-2048,col_off=c[1]-2048,height=4096,width=4096)))
            sources = []
            for size, win in windows:
                target = OUT / f"{asset['site']}-{size}.npz"
                if target.exists():
                    raise ValueError('Refuse overwrite scientific source')
                raw = dataset.read(1, window=Window(**win)); mask = raw == 65535
                if raw.shape != (size,size) or np.any(raw[~mask] > 10000):
                    raise ValueError('Window/range without resampling')
                np.savez_compressed(target, raw=raw, mask=mask)
                sources.append(dict(source=str(target.relative_to(ROOT)), source_sha256=sha(target),
                    shape=list(raw.shape), missing=int(mask.sum()), valid=int((~mask).sum()),
                    raw_uint16_sha256=hashlib.sha256(raw.astype('<u2').tobytes()).hexdigest(),
                    window=win, geo=dict(crs=dataset.crs.to_wkt(),
                        affine=list(dataset.window_transform(Window(**win)))[:6], units='m2',
                        product='GHS-BUILT-S R2023A E2020', resampling=False)))
        result.update(status='PASS_NATIVE_SOURCE', sources=sources, archive_sha256=sha(archive),
                      archive_bytes=archive.stat().st_size)
    except Exception as e:
        result['error'] = type(e).__name__ + ': ' + str(e)
    return result


def run():
    assets = json.loads(ASSETS.read_text())
    if OUT.exists():
        raise ValueError('Fresh acquisition directory required')
    head = subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    if subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True):
        raise ValueError('Clean committed protocol required')
    remote = subprocess.check_output(['git','-C',str(ROOT),'ls-remote','origin','refs/heads/main'],text=True).split()[0]
    if head != remote:
        raise ValueError('Pushed protocol required')
    OUT.mkdir(); started=time.perf_counter()
    unique = {a['tile']:a for a in assets['sites']}
    # Only independent network transfers overlap; extraction is sequential.
    with ThreadPoolExecutor(max_workers=3) as pool:
        for path in pool.map(fetch, unique.values()):
            print('downloaded',path.name,flush=True)
    rows=[]
    for asset in assets['sites']:
        rows.append(acquire_site(asset))
        report = dict(status='RUNNING', launch_commit=head, assets_sha256=sha(ASSETS), rows=rows,
                      seconds=time.perf_counter()-started, gpu_used=False, no_resampling=True)
        save(OUT/'manifest.json',report)
        print(asset['site'], rows[-1]['status'],rows[-1].get('error'),flush=True)
    report['status'] = 'PASS_40_NATIVE_LOCATIONS' if all(r['status']=='PASS_NATIVE_SOURCE' for r in rows) else 'PARTIAL'
    save(OUT/'manifest.json',report)
    if report['status'] != 'PASS_40_NATIVE_LOCATIONS':
        raise SystemExit(2)


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['freeze','run'])
    args=p.parse_args(); freeze() if args.action=='freeze' else run()
