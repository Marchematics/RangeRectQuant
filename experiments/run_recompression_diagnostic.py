"""Frozen homogeneous recompression falsifier; not a new quantizer."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np
from controls.field_packet import encode as greedy_encode
from controls.viable_greedy import reconstruct as greedy_reconstruct
from range_rect_quant.packet import encode as dp_encode, SETTINGS
from run_pilot import ROOT, PREFLIGHT as AB_PREFLIGHT, sha, write_json, git, verify_preserved, sources
from verify_saved import independent_rectangle_max

PREFLIGHT = ROOT / 'integration/checks/recompression_preflight_20261001.json'
CONTROL_PREFLIGHT = ROOT / 'integration/checks/viable_greedy_preflight_20261001.json'
ENV = dict(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
           PYTHONPATH=os.pathsep.join(map(str, (ROOT, ROOT / 'src', ROOT / 'experiments'))))


def initial_cases():
    rows = []
    for family, path in (('dp', ROOT / 'results/pilot_20261001/ledger.json'),
                         ('greedy', ROOT / 'results/viable_greedy_20261001/ledger.json')):
        for row in json.loads(path.read_text()):
            if family == 'dp' and row['mode'] in ('lossy', 'identity'):
                rows.append(dict(row, algorithm='identity' if row['mode'] == 'identity' else 'dp'))
            elif family == 'greedy' and row['mode'] == 'lossy' and row['algorithm_id'] == 1:
                rows.append(dict(row, algorithm='greedy'))
    if len(rows) != 24:
        raise ValueError('Initial fixed cases')
    return sorted(rows, key=lambda r: (r['algorithm'], r['site'], r['step']))


def encode_step(x, mask, step, algorithm, geo):
    if algorithm in ('dp', 'identity'):
        return dp_encode(x, mask, step, 'identity' if algorithm == 'identity' else 'lossy', geo)
    if algorithm != 'greedy':
        raise ValueError('Fixed algorithm')
    y, mechanism = greedy_reconstruct(x, SETTINGS[step][1], step, 10000, mask)
    packet, body, info = greedy_encode(x, y, mask, step, 'lossy', 1, geo)
    return packet, body, dict(info, quantizer=mechanism)


def check_bindings(preflight):
    count = 0
    for group in ('files', 'runtimes'):
        for name, expected in preflight[group].items():
            if sha(ROOT / name if group == 'files' else Path(name)) != expected:
                raise ValueError('Frozen binding: ' + name)
            count += 1
    return count


def freeze():
    if PREFLIGHT.exists():
        raise SystemExit('Refuse overwrite preflight')
    original, control = [json.loads(p.read_text()) for p in (AB_PREFLIGHT, CONTROL_PREFLIGHT)]
    check_bindings(original); check_bindings(control)
    files = dict(control['files'])
    paths = [Path(__file__), ROOT / 'tests/test_recompression_diagnostic.py',
             ROOT / 'docs/RECOMPRESSION_DIAGNOSTIC_PROTOCOL_20261001.md',
             ROOT / 'integration/checks/recompression_tests_20261001.log',
             AB_PREFLIGHT, CONTROL_PREFLIGHT,
             ROOT / 'results/pilot_20261001/ledger.json',
             ROOT / 'results/viable_greedy_20261001/ledger.json']
    for row in initial_cases():
        for key in ('packet', 'body', 'output', 'worker_report'):
            path = ROOT / row[key]
            if sha(path) != row[key + '_sha256']:
                raise ValueError('Initial artifact')
            paths.append(path)
    files.update({str(p.relative_to(ROOT)): sha(p) for p in paths})
    write_json(PREFLIGHT, dict(status='PASS_FROZEN_RECOMPRESSION_DIAGNOSTIC', files=files,
        runtimes=original['runtimes'], environment=ENV, preserved=verify_preserved(),
        initial_cases=24, planned_primary_new_packets=112, planned_identity_new_packets=8,
        planned_maximum_new_packets=120, observed_development_only=True,
        no_new_real_encoding_during_freeze=True, quantizers_unchanged=True))


def summarize(rows, elapsed):
    gates, groups = [], []
    for algorithm in ('dp', 'greedy'):
        for epsilon, step in ((100, 20), (1000, 200)):
            selected = [r for r in rows if r['algorithm'] == algorithm and r['step'] == step]
            final = [r for r in selected if r['pass'] == 8 and r['status'] == 'DECODED_AND_AUDITED']
            complete = len(selected) == 28 and len(final) == 4 and all(r['status'] == 'DECODED_AND_AUDITED' for r in selected)
            local = complete and all(r['local_maximum'] <= epsilon for r in selected)
            violations = sum(r['cumulative_maximum'] > epsilon for r in final)
            gates.append(dict(algorithm=algorithm, epsilon=epsilon, complete=complete,
                all_local_legal=local, pass8_cumulative_violations=violations,
                sources=4, passed=bool(local and violations >= 3)))
            groups.append(dict(algorithm=algorithm, epsilon=epsilon,
                selected_checks=[{k: r[k] for k in ('site', 'pass', 'packet_bytes', 'fine',
                    'changed_from_previous', 'local_maximum', 'cumulative_maximum')}
                    for r in selected if r['pass'] in (2, 4, 8) and r['status'] == 'DECODED_AND_AUDITED']))
    by_algorithm = {a: all(g['passed'] for g in gates if g['algorithm'] == a) for a in ('dp', 'greedy')}
    good = [r for r in rows if r['status'] == 'DECODED_AND_AUDITED']
    return dict(status='COMPLETE' if len(rows) == 120 and len(good) == 120 else 'PARTIAL',
        attempted_new_packets=len(rows), fresh_sourcefree_decodes=len(good),
        exceptions=sum(r['status'] == 'EXCEPTION' for r in rows),
        verdicts=dict(Counter('LEGAL' if r[k] <= SETTINGS[r['step']][0] else 'ILLEGAL'
            for r in good for k in ('local_maximum', 'cumulative_maximum'))),
        groups=groups, serious_drift_gates=gates, serious_drift_algorithm_pass=by_algorithm,
        first_recompression_non_idempotent=sum(r['changed_from_previous'] > 0 for r in good
            if r['pass'] == 2 and r['algorithm'] != 'identity'),
        identity_actual_pass2_decodes=sum(r['algorithm'] == 'identity' for r in good),
        identity_pass3_to8_not_run=True, elapsed_seconds=elapsed, gpu_used=False,
        new_sources=0, refinement_added=False, quantizers_modified=False,
        novelty_established=False, sota_established=False, full_goal_completed=False)


def run(out):
    if out.exists() or not out.is_relative_to(ROOT / 'results'):
        raise SystemExit('Need fresh result directory')
    if git('status', '--porcelain') or git('ls-remote', 'origin', 'refs/heads/main').split()[0] != git('rev-parse', 'HEAD'):
        raise SystemExit('Need clean pushed tree')
    preflight = json.loads(PREFLIGHT.read_text())
    check_bindings(preflight); verify_preserved()
    source_map = {s['site']: s for s in sources()}
    query_rectangles = np.load(ROOT / 'data/queries.npy', allow_pickle=False)
    out.mkdir(parents=True)
    for name in ('packets', 'bodies', 'decodes', 'workers', 'attempts'):
        (out / name).mkdir()
    write_json(out / 'launch.json', dict(commit=git('rev-parse', 'HEAD'), clean_pushed_tree=True,
        preflight_sha256=sha(PREFLIGHT), environment=ENV,
        started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
    started = time.perf_counter()
    rows = []
    for base in initial_cases():
        source = source_map[base['site']]
        input_path = ROOT / base['output']
        input_sha = base['output_sha256']
        for generation in range(2, 3 if base['algorithm'] == 'identity' else 9):
            if time.perf_counter() - started > 900:
                write_json(out / 'report.json', summarize(rows, time.perf_counter() - started))
                raise TimeoutError('Frozen whole-matrix limit; partial retained')
            stem = f"{base['site']}-q{base['step']}-{base['algorithm']}-p{generation}"
            row = dict(id=stem, algorithm=base['algorithm'], site=base['site'], step=base['step'],
                pass_number=generation, status='EXCEPTION', input=str(input_path.relative_to(ROOT)),
                input_sha256=input_sha, original_source_sha256=source['source_sha256'])
            row['pass'] = row.pop('pass_number')
            try:
                if sha(input_path) != input_sha:
                    raise ValueError('Previous decoded field hash')
                with np.load(input_path, allow_pickle=False) as bundle:
                    current = bundle['y']
                    if current.dtype != np.float64 or not np.array_equal(current, np.rint(current)):
                        raise ValueError('Integer previous field')
                    np.testing.assert_array_equal(bundle['mask'], source['mask'])
                current = current.astype(np.int64)
                before = time.perf_counter()
                packet, body, info = encode_step(current, source['mask'], base['step'], base['algorithm'], source['geo'])
                row.update(info, packet_bytes=len(packet), encode_seconds=time.perf_counter() - before)
                if sum(info['fees'].values()) != len(packet):
                    raise ValueError('Complete fees')
                for key, raw, directory, suffix in (('packet', packet, 'packets', '.packet'), ('body', body, 'bodies', '.body')):
                    target = out / directory / (stem + suffix); target.write_bytes(raw)
                    row[key], row[key + '_sha256'] = str(target.relative_to(ROOT)), sha(target)
                decoded = out / 'decodes' / (stem + '.npz')
                worker_report = out / 'workers' / (stem + '.json')
                worker = 'controls/worker.py' if base['algorithm'] == 'greedy' else 'experiments/worker.py'
                argv = [sys.executable, str(ROOT / worker), str(ROOT / row['packet']),
                        str(decoded), str(worker_report), '--queries', str(ROOT / 'data/queries.npy')]
                process = subprocess.run(argv, cwd=ROOT, env=dict(os.environ, **ENV), capture_output=True, text=True, timeout=120)
                for suffix, text in (('stdout', process.stdout), ('stderr', process.stderr)):
                    (out / 'workers' / (stem + '.' + suffix + '.log')).write_text(text)
                row.update(worker_argv=argv, worker_returncode=process.returncode)
                if process.returncode:
                    raise ValueError('Cold source-free worker')
                with np.load(decoded, allow_pickle=False) as bundle:
                    y, mask = bundle['y'], bundle['mask']
                if (y.dtype != np.float64 or not np.array_equal(y, np.rint(y)) or np.any((y < 0) | (y > 10000)) or
                        not np.array_equal(mask, source['mask']) or y[mask].any()):
                    raise ValueError('Physical field/mask')
                y = y.astype(np.int64)
                local = y - current
                row.update(local_maximum=int(independent_rectangle_max(local)),
                    cumulative_maximum=int(independent_rectangle_max(y - source['x'])),
                    local_max_abs_prefix=int(np.abs(local.cumsum(0).cumsum(1)).max()),
                    changed_from_previous=int(np.count_nonzero(local)),
                    changed_from_original=int(np.count_nonzero(y - source['x'])),
                    fine=int(np.count_nonzero(y % base['step'])))
                epsilon, band = SETTINGS[base['step']]
                if row['local_maximum'] > epsilon or row['local_max_abs_prefix'] > band:
                    raise ValueError('Local original guarantee')
                if base['algorithm'] == 'identity' and row['changed_from_previous']:
                    raise ValueError('Identity control')
                saved_worker = json.loads(worker_report.read_text())
                if saved_worker['source_provided'] or saved_worker['prefix_state_provided'] or len(saved_worker['answers']) != 1024:
                    raise ValueError('Source-free service')
                if saved_worker['meta']['geo'] != source['geo']:
                    raise ValueError('Geospatial metadata')
                for index, rectangle in enumerate(query_rectangles):
                    a, b, c, d = map(int, rectangle)
                    n = int((~mask[a:b, c:d]).sum())
                    answer = dict(sum=float(y[a:b, c:d].sum()) if n else None, count=n)
                    if saved_worker['answers'][index] != answer:
                        raise ValueError('Direct slice query')
                row['direct_queries_checked'] = 1024
                row['status'] = 'DECODED_AND_AUDITED'
                for key, target in (('output', decoded), ('worker_report', worker_report)):
                    row[key], row[key + '_sha256'] = str(target.relative_to(ROOT)), sha(target)
                input_path, input_sha = decoded, row['output_sha256']
            except Exception:
                row['exception'] = traceback.format_exc()
            rows.append(row)
            write_json(out / 'attempts' / (stem + '.json'), row)
            write_json(out / 'ledger.json', rows)
            write_json(out / 'report.json', summarize(rows, time.perf_counter() - started))
            print(stem, row['status'], row.get('cumulative_maximum'), row.get('fine'), flush=True)
            if row['status'] != 'DECODED_AND_AUDITED':
                break
    verify_preserved(); check_bindings(preflight)
    print(json.dumps(summarize(rows, time.perf_counter() - started), indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.freeze:
        freeze()
    elif args.out:
        run(args.out.resolve())
    else:
        parser.error('--freeze or --out required')


if __name__ == '__main__':
    main()
