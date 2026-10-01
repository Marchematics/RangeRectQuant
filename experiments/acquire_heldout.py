"""Metadata-frozen new geography acquisition; no method tuning or encoding."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT.parent / 'LinewiseROI'
PREFLIGHT = ROOT / 'integration/checks/heldout_acquisition_preflight_20261001.json'
ASSETS = ROOT / 'integration/heldout_assets_20261001.json'
sys.path.append(str(LEGACY / 'experiments'))
from built_area_acquire import download, validate_window


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def validate_assets(assets):
    expected = {'cairo': (31.2357, 30.0444), 'delhi': (77.2090, 28.6139),
                'new_york': (-74.0060, 40.7128), 'jakarta': (106.8456, -6.2088)}
    if len(assets) != 4 or {a['name'] for a in assets} != set(expected):
        raise ValueError('Frozen four new sites')
    for asset in assets:
        validate_window(asset)
        if (asset['longitude'], asset['latitude']) != expected[asset['name']]:
            raise ValueError('Frozen coordinates')
        x, y = asset['projected_point_m']
        if (asset['window']['col_off'] != int((x - asset['left']) // 100) - 256 or
                asset['window']['row_off'] != int((asset['top'] - y) // 100) - 256):
            raise ValueError('Centered native selection')


def check_bindings(frozen):
    for name, expected in frozen['files'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('Acquisition source binding: ' + name)
    for name, expected in frozen['runtimes'].items():
        if sha(Path(name)) != expected:
            raise ValueError('Acquisition runtime binding: ' + name)


def freeze():
    import rasterio._base
    import pyproj._crs
    if PREFLIGHT.exists():
        raise SystemExit('Refusing to overwrite acquisition freeze')
    assets = json.loads(ASSETS.read_text())['sites']
    validate_assets(assets)
    previous = json.loads((ROOT / 'integration/checks/recompression_preflight_20261001.json').read_text())
    check_bindings(previous)
    files = dict(previous['files'])
    for path in (Path(__file__), ASSETS, ROOT / 'docs/HOLDOUT_PROTOCOL_20261001.md',
                 ROOT / 'tests/test_heldout_acquisition.py',
                 ROOT / 'integration/checks/heldout_acquisition_tests_20261001.log',
                 LEGACY / 'experiments/built_area_acquire.py'):
        name = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        files[name] = sha(path)
    runtimes = dict(previous['runtimes'])
    for path in (Path(sys.executable).resolve(), Path(np._core._multiarray_umath.__file__),
                 Path(rasterio._base.__file__), Path(pyproj._crs.__file__)):
        runtimes[str(path)] = sha(path)
    write(PREFLIGHT, dict(status='FROZEN_BEFORE_NEW_GEOGRAPHY_PIXELS', files=files,
                          runtimes=runtimes, sites=[a['name'] for a in assets],
                          planned_sources=4, pixels_acquired=False, method_encoded=False))


def acquire(out):
    import rasterio
    from rasterio.windows import Window
    from pyproj import CRS
    cache = ROOT / '.acquisition/heldout_20261001'
    if out.exists() or cache.exists() or not out.is_relative_to(ROOT / 'data'):
        raise SystemExit('Fresh source and archive directories required')
    frozen = json.loads(PREFLIGHT.read_text()); check_bindings(frozen)
    git = lambda *args: subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()
    revision = git('rev-parse', 'HEAD')
    if git('status', '--porcelain') or git('ls-remote', 'origin', 'refs/heads/main').split()[0] != revision:
        raise SystemExit('Need clean pushed acquisition snapshot')
    assets = json.loads(ASSETS.read_text())['sites']; validate_assets(assets)
    out.mkdir(parents=True); cache.mkdir(parents=True)
    rows = []; started = time.perf_counter()
    for asset in assets:
        row = dict(site=asset['name'], asset=asset, status='FAIL')
        try:
            archive = download(asset, cache)
            row.update(archive_sha256=sha(archive), archive_bytes=archive.stat().st_size,
                       archive_local=str(archive.relative_to(ROOT)))
            with zipfile.ZipFile(archive) as bundle:
                if bundle.testzip() is not None:
                    raise ValueError('Archive CRC')
                names = [n for n in bundle.namelist() if n.lower().endswith('.tif')]
                if len(names) != 1 or any('..' in Path(n).parts for n in bundle.namelist()):
                    raise ValueError('Unique safe native TIFF')
            with rasterio.open(f'/vsizip/{archive.resolve()}/{names[0]}') as dataset:
                expected_affine = (100., 0., float(asset['left']), 0., -100., float(asset['top']))
                if (dataset.count != 1 or dataset.dtypes != ('uint16',) or dataset.nodata != 65535 or
                        dataset.shape != tuple(asset['expected_tile_shape']) or
                        CRS(dataset.crs) != CRS.from_user_input('ESRI:54009') or
                        tuple(dataset.transform)[:6] != expected_affine):
                    raise ValueError('Native product/geometry contract')
                window = Window(**asset['window']); raw = dataset.read(1, window=window)
                mask = raw == 65535
                if raw.shape != (512, 512) or raw.dtype != np.uint16 or np.any(raw[~mask] > 10000):
                    raise ValueError('Bounded native UInt16 field')
                target = out / (asset['name'] + '.npz')
                np.savez_compressed(target, raw=raw, mask=mask)
                row.update(status='PASS_NATIVE_UNRESAMPLED_NEW_GEOGRAPHY',
                           source=str(target.relative_to(ROOT)), source_sha256=sha(target),
                           raw_uint16_sha256=hashlib.sha256(raw.astype('<u2').tobytes()).hexdigest(),
                           mask_sha256=hashlib.sha256(mask.tobytes()).hexdigest(),
                           valid_samples=int((~mask).sum()), nodata_samples=int(mask.sum()),
                           valid_zeros=int(np.count_nonzero((raw == 0) & ~mask)),
                           geo=dict(crs_wkt=dataset.crs.to_wkt(), affine=list(dataset.window_transform(window))[:6],
                                    epoch=2020, product='GHS-BUILT-S R2023A', native_resolution_m=100),
                           resampling=False, method_encoded=False)
            http = cache / (asset['name'] + '-http.json')
            (out / http.name).write_bytes(http.read_bytes())
        except Exception:
            row['exception'] = traceback.format_exc()
        rows.append(row)
        complete = len(rows) == 4 and all(r['status'].startswith('PASS_') for r in rows)
        write(out / 'manifest.json', dict(status='PASS_FOUR_NEW_NATIVE_SOURCES' if complete else 'PARTIAL',
                                          launch_commit=revision, preflight_sha256=sha(PREFLIGHT),
                                          rows=rows, elapsed_seconds=time.perf_counter() - started,
                                          method_encoded=False, gpu_used=False))
        print(asset['name'], row['status'], row.get('archive_bytes'), row.get('exception', ''), flush=True)
    check_bindings(frozen)
    if not complete:
        raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.freeze:
        freeze()
    elif args.out:
        acquire(args.out.resolve())
    else:
        parser.error('--freeze or --out required')


if __name__ == '__main__':
    main()
