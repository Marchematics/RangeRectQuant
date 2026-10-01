"""Post-package relocated source-free replay, in the original Python runtime."""
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Refusing to overwrite delivery verification')
    start = time.perf_counter()
    cases, queries_checked = [], 0
    with tempfile.TemporaryDirectory(prefix='rangerect-delivery-') as directory:
        temporary = Path(directory)
        with zipfile.ZipFile(args.archive) as bundle:
            names = bundle.namelist()
            if (len(set(names)) != len(names) or bundle.testzip() is not None or
                    any(Path(n).is_absolute() or '..' in Path(n).parts for n in names)):
                raise ValueError('Unsafe/duplicate/invalid ZIP')
            manifest = json.loads(bundle.read('PACKAGE_MANIFEST.json'))
            for row in manifest['entries']:
                data = bundle.read(row['path'])
                if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                    raise ValueError('Archive payload hash')
            bundle.extractall(temporary)
        root = temporary/'RangeRectQuant'
        output = temporary/'new-decodes'
        output.mkdir()
        environment = dict(os.environ, PYTHONPATH=str(root/'src')+os.pathsep+str(root/'experiments'),
                           CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
        queries = np.load(root/'data/queries.npy', allow_pickle=False)
        ledger = json.loads((root/'results/pilot_20261001/ledger.json').read_text())
        for row in ledger:
            field = output/(row['id']+'.npz')
            worker_report = output/(row['id']+'.json')
            argv = [sys.executable, str(root/'experiments/worker.py'), str(root/row['packet']),
                    str(field), str(worker_report), '--queries', str(root/'data/queries.npy')]
            process = subprocess.run(argv, cwd=root, env=environment, capture_output=True, text=True, timeout=120)
            if process.returncode:
                raise ValueError('Relocated worker failed: '+process.stderr)
            worker = json.loads(worker_report.read_text())
            if worker['source_provided'] or worker['prefix_state_provided']:
                raise ValueError('Decoder dependency')
            with np.load(field, allow_pickle=False) as decoded:
                y, mask, zero = decoded['y'], decoded['mask'], decoded['zero_protect']
            with np.load(root/row['output'], allow_pickle=False) as saved:
                if not all(np.array_equal(value, saved[key]) for value, key in
                           ((y, 'y'), (mask, 'mask'), (zero, 'zero_protect'))):
                    raise ValueError('Relocated output differs from audited field')
            if y.dtype != np.float64 or np.any(y != np.rint(y)) or np.any((y < 0) | (y > 10000)):
                raise ValueError('Decoded integer/range')
            for index, rectangle in enumerate(queries):
                a, b, c, d = map(int, rectangle)
                count = int((~mask[a:b, c:d]).sum())
                answer = dict(sum=float(y[a:b, c:d].sum()) if count else None, count=count)
                if worker['answers'][index] != answer:
                    raise ValueError('Independent archive direct-slice answer')
                queries_checked += 1
            cases.append(dict(id=row['id'], saved_arrays_equal=True, sourcefree_interface=True))
            print(row['id'], 'ARCHIVE_DECODE_PASS', flush=True)
        if len(cases) != 24 or queries_checked != 24576:
            raise ValueError('Incomplete frozen matrix')
    receipt = dict(
        status='PASS_ARCHIVE_RELOCATED_SOURCEFREE_DECODE',
        archive=str(args.archive.resolve()),
        archive_sha256=hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        source_commit=manifest['source_commit'], payload_hashes_checked=manifest['payload_files'],
        fresh_relocated_sourcefree_decodes=len(cases), direct_slice_queries_checked=queries_checked,
        cases=cases, elapsed_seconds=time.perf_counter()-start,
        original_runtime_new_file_location=True, new_machine_or_os_tested=False,
        repeated_all_rectangle_algorithm=False, all_rectangle_link='Decoded arrays identical to already independently audited fields',
        full_historical_audit_standalone=False, new_optimizer_runs=0, new_sources=0,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.out.write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
    print('PASS 24 relocated source-free decodes, 24576 direct queries', flush=True)


if __name__ == '__main__':
    main()
