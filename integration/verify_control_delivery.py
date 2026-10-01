"""Relocated fresh decoding of all 56 saved paid fields; no source to workers."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import zipfile

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Refusing to overwrite verification')
    started = time.perf_counter()
    cases, query_count = [], 0
    with tempfile.TemporaryDirectory(prefix='rangerect-control-delivery-') as directory:
        temporary = Path(directory)
        with zipfile.ZipFile(args.archive) as bundle:
            names = bundle.namelist()
            if (len(set(names)) != len(names) or bundle.testzip() is not None or
                    any(Path(n).is_absolute() or '..' in Path(n).parts for n in names)):
                raise ValueError('Unsafe/duplicate/invalid ZIP')
            manifest = json.loads(bundle.read('PACKAGE_MANIFEST.json'))
            for row in manifest['entries']:
                raw = bundle.read(row['path'])
                if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                    raise ValueError('Payload SHA')
            bundle.extractall(temporary)
        root = temporary / 'RangeRectQuant'
        output = temporary / 'new-decodes'
        output.mkdir()
        environment = dict(os.environ,
            PYTHONPATH=os.pathsep.join(map(str, (root, root / 'src', root / 'experiments'))),
            CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
        queries = np.load(root / 'data/queries.npy', allow_pickle=False)
        for family, result, worker_script, count in (
            ('RQ01', 'pilot_20261001', 'experiments/worker.py', 24),
            ('QF01', 'viable_greedy_20261001', 'controls/worker.py', 32),
        ):
            rows = json.loads((root / 'results' / result / 'ledger.json').read_text())
            if len(rows) != count:
                raise ValueError('Incomplete family')
            for row in rows:
                stem = family + '-' + row['id']
                field, report = output / (stem + '.npz'), output / (stem + '.json')
                argv = [sys.executable, str(root / worker_script), str(root / row['packet']),
                        str(field), str(report), '--queries', str(root / 'data/queries.npy')]
                process = subprocess.run(argv, cwd=root, env=environment, capture_output=True, text=True, timeout=120)
                if process.returncode:
                    raise ValueError('Relocated worker: ' + process.stderr)
                worker = json.loads(report.read_text())
                if worker['source_provided'] or worker['prefix_state_provided']:
                    raise ValueError('Worker dependencies')
                with np.load(field, allow_pickle=False) as decoded:
                    y, mask, zero = decoded['y'], decoded['mask'], decoded['zero_protect']
                with np.load(root / row['output'], allow_pickle=False) as saved:
                    if not all(np.array_equal(v, saved[k]) for v, k in
                               ((y, 'y'), (mask, 'mask'), (zero, 'zero_protect'))):
                        raise ValueError('Relocated field differs from independently audited field')
                if y.dtype != np.float64 or np.any(y != np.rint(y)) or np.any((y < 0) | (y > 10000)):
                    raise ValueError('Integer/range')
                if len(worker['answers']) != len(queries):
                    raise ValueError('Incomplete query service')
                for index, rectangle in enumerate(queries):
                    a, b, c, d = map(int, rectangle)
                    valid = ~mask[a:b, c:d]
                    n = int(valid.sum())
                    answer = dict(sum=float(y[a:b, c:d][valid].sum()) if n else None, count=n)
                    if worker['answers'][index] != answer:
                        raise ValueError('Independent direct-slice answer')
                    query_count += 1
                cases.append(dict(family=family, id=row['id'], saved_arrays_equal=True, sourcefree_interface=True))
                print(stem, 'ARCHIVE_DECODE_PASS', flush=True)
        if len(cases) != 56 or query_count != 57344:
            raise ValueError('Incomplete fixed matrix')
    receipt = dict(status='PASS_RELOCATED_56_SOURCEFREE_PAID_FIELD_DECODES',
        archive=str(args.archive.resolve()), archive_sha256=hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        source_commit=manifest['source_commit'], payload_hashes_checked=manifest['payload_files'],
        fresh_relocated_sourcefree_decodes=56, direct_slice_queries_checked=query_count,
        cases=cases, elapsed_seconds=time.perf_counter() - started,
        original_runtime_new_file_location=True, new_machine_or_os_tested=False,
        repeated_all_rectangle_algorithm=False,
        all_rectangle_link='Decoded arrays equal the independently audited saved fields',
        full_historical_audit_standalone=False, new_optimizer_runs=0, new_sources=0,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.out.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print('PASS 56 fresh relocated decodes / 57344 direct queries', flush=True)


if __name__ == '__main__':
    main()
