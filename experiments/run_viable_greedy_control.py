"""One frozen same-carrier necessity control on already observed sources."""
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
from controls.field_packet import encode
from controls.viable_greedy import reconstruct, row_greedy
from range_rect_quant.packet import SETTINGS
from built_area_integer_metrics import integer_error, contract
from run_pilot import ROOT, PREFLIGHT as ORIGINAL, sha, write_json, git, sources, verify_preserved
from verify_saved import independent_rectangle_max

PREFLIGHT = ROOT/'integration/checks/viable_greedy_preflight_20261001.json'
SAVED = ROOT/'results/pilot_20261001'
ENVIRONMENT = dict(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                   PYTHONPATH=os.pathsep.join(map(str, (ROOT, ROOT/'src', ROOT/'experiments'))))


def verify_original():
    preflight = json.loads(ORIGINAL.read_text())
    for group in ('files', 'runtimes'):
        for name, expected in preflight[group].items():
            if sha(ROOT/name if group == 'files' else Path(name)) != expected:
                raise ValueError('Original binding changed: '+name)
    return verify_preserved()


def freeze():
    if PREFLIGHT.exists():
        raise SystemExit('Refusing to overwrite preflight')
    original = json.loads(ORIGINAL.read_text())
    names = dict(original['files'])
    files = [*sorted((ROOT/'controls').glob('*.py')), Path(__file__),
             ROOT/'tests/test_viable_greedy.py', ROOT/'docs/VIABLE_GREEDY_CONTROL_PROTOCOL_20261001.md',
             ROOT/'integration/checks/viable_greedy_tests_attempt1_20261001.log',
             ROOT/'integration/checks/viable_greedy_tests_attempt2_20261001.log',
             SAVED/'ledger.json', SAVED/'report.json']
    ledger = json.loads((SAVED/'ledger.json').read_text())
    for row in ledger:
        if row['mode'] == 'identity':
            continue
        for key in ('packet', 'body', 'output', 'worker_report'):
            path = ROOT/row[key]
            if sha(path) != row[key+'_sha256']:
                raise ValueError('Original field evidence hash')
            files.append(path)
    names.update({str(path.relative_to(ROOT)): sha(path) for path in files})
    write_json(PREFLIGHT, dict(
        status='PASS_FROZEN_VIABLE_GREEDY_CONTROL_PREFLIGHT', files=names,
        runtimes=original['runtimes'], environment=ENVIRONMENT, preserved=verify_original(),
        original_report_sha256=sha(SAVED/'report.json'), planned_packets=32,
        planned_budget_verdicts=64, planned_global_greedy_constructions=16,
        no_real_greedy_construction_during_freeze=True, no_new_sources=True))


def summary(rows, elapsed):
    groups, gates = [], []
    for step in (20, 200):
        epsilon = SETTINGS[step][0]
        for mode in ('lossy', 'zero-preserve'):
            selected = [row for row in rows if row['step'] == step and row['mode'] == mode]
            pairs = []
            for site in ('paris', 'tokyo', 'lagos', 'sao_paulo'):
                dp = next((r for r in selected if r['site'] == site and r['algorithm_id'] == 0), None)
                greedy = next((r for r in selected if r['site'] == site and r['algorithm_id'] == 1), None)
                if dp is None or greedy is None or any(r['status'] != 'DECODED_AND_AUDITED' for r in (dp, greedy)):
                    continue
                legal = all(r['contracts'][str(epsilon)]['status'] == 'LEGAL' for r in (dp, greedy))
                pairs.append(dict(site=site, legal=legal, dp_bytes=dp['packet_bytes'],
                    greedy_bytes=greedy['packet_bytes'], dp_body_bytes=dp['fees']['body_bytes'],
                    greedy_body_bytes=greedy['fees']['body_bytes'], dp_fine=dp['fine'], greedy_fine=greedy['fine'],
                    dp_reduction_from_greedy=1-dp['packet_bytes']/greedy['packet_bytes'],
                    dp_nontrivial=dp['contracts'][str(epsilon)]['changed_values'] > 0,
                    greedy_nontrivial=greedy['contracts'][str(epsilon)]['changed_values'] > 0))
            dp_total = sum(p['dp_bytes'] for p in pairs)
            greedy_total = sum(p['greedy_bytes'] for p in pairs)
            group = dict(epsilon=epsilon, mode=mode, pairs=pairs, dp_bytes=dp_total, greedy_bytes=greedy_total,
                dp_reduction_from_greedy=None if not greedy_total else 1-dp_total/greedy_total,
                dp_fine=sum(p['dp_fine'] for p in pairs), greedy_fine=sum(p['greedy_fine'] for p in pairs))
            groups.append(group)
            if mode == 'lossy':
                wins = sum(p['dp_bytes'] < p['greedy_bytes'] for p in pairs)
                expansion = max([max(0, p['dp_bytes']/p['greedy_bytes']-1) for p in pairs], default=0)
                passed = (len(pairs) == 4 and all(p['legal'] and p['dp_nontrivial'] for p in pairs) and
                          wins >= 3 and dp_total <= .9*greedy_total and expansion <= .05)
                gates.append(dict(epsilon=epsilon, passed=passed, strict_dp_wins=wins,
                    complete_pairs=len(pairs), maximum_source_dp_expansion_fraction=expansion,
                    dp_reduction_from_greedy=group['dp_reduction_from_greedy']))
    statuses = Counter(v['status'] for r in rows for v in r.get('contracts', {}).values())
    return dict(status='COMPLETE_FROZEN_VIABLE_GREEDY_CONTROL' if len(rows) == 32 else 'PARTIAL',
        planned_packets=32, attempted_packets=len(rows),
        fresh_sourcefree_decodes=sum(r['status'] == 'DECODED_AND_AUDITED' for r in rows),
        exception_packets=sum(r['status'] == 'EXCEPTION' for r in rows), budget_verdicts=sum(statuses.values()),
        verdicts=dict(statuses), groups=groups, dp_necessity_gates=gates, elapsed_seconds=elapsed,
        no_new_sources=True, previously_observed_development_sources=True, gpu_used=False,
        main_quantizer_modified=False, novelty_established=False, sota_established=False,
        full_goal_completed=False)


def run(out):
    if out.exists() or not out.is_relative_to(ROOT/'results'):
        raise SystemExit('Need a new results directory')
    if git('status', '--porcelain') or git('ls-remote', 'origin', 'refs/heads/main').split()[0] != git('rev-parse', 'HEAD'):
        raise SystemExit('Need clean pushed tree')
    preflight = json.loads(PREFLIGHT.read_text())
    for group in ('files', 'runtimes'):
        for name, expected in preflight[group].items():
            if sha(ROOT/name if group == 'files' else Path(name)) != expected:
                raise ValueError('Frozen control binding: '+name)
    verify_original()
    records = sources()
    saved = {r['id']: r for r in json.loads((SAVED/'ledger.json').read_text())}
    q = np.load(ROOT/'data/queries.npy', allow_pickle=False)
    out.mkdir(parents=True)
    for name in ('packets', 'bodies', 'decodes', 'workers', 'attempts'):
        (out/name).mkdir()
    write_json(out/'launch.json', dict(commit=git('rev-parse', 'HEAD'), clean_pushed_tree=True,
        preflight_sha256=sha(PREFLIGHT), environment=ENVIRONMENT, started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
    started = time.perf_counter()
    rows = []
    for source in records:
        for step in (20, 200):
            for mode in ('lossy', 'zero-preserve'):
                original = saved[f"{source['site']}-q{step}-{mode}"]
                protected = source['mask'] | ((source['x'] == 0) & ~source['mask'] if mode == 'zero-preserve' else False)
                for algorithm in (0, 1):
                    if time.perf_counter()-started > 1800:
                        raise TimeoutError('Overall frozen control limit; partial records retained')
                    name = f"{source['site']}-q{step}-{mode}-a{algorithm}"
                    row = dict(id=name, site=source['site'], step=step, mode=mode, algorithm_id=algorithm,
                               status='EXCEPTION', source=source['local_source'], source_sha256=source['source_sha256'])
                    began = time.perf_counter()
                    try:
                        if algorithm == 0:
                            with np.load(ROOT/original['output'], allow_pickle=False) as bundle:
                                field = bundle['y'].astype(np.int64)
                            row['construction_seconds'] = None
                            row['saved_dp_output_sha256'] = original['output_sha256']
                            prefix = (field-source['x']).cumsum(0).cumsum(1)
                            conditional_greedy = []
                            for i in range(len(field)):
                                up = prefix[i-1] if i else np.zeros(field.shape[1], np.int64)
                                _, _, count, _ = row_greedy(source['x'][i], up, SETTINGS[step][1], step, 10000, protected[i])
                                if count < original['quantizer']['row_min_off_lattice'][i]:
                                    raise ValueError('Greedy contradicted exact conditional DP minimum')
                                conditional_greedy.append(int(count))
                            row['greedy_fine_at_same_dp_incoming_rows'] = conditional_greedy
                        else:
                            before = time.perf_counter()
                            field, info = reconstruct(source['x'], SETTINGS[step][1], step, 10000, protected)
                            row['construction_seconds'] = time.perf_counter()-before
                            row['greedy_info'] = info
                        before = time.perf_counter()
                        packet, body, info = encode(source['x'], field, source['mask'], step, mode, algorithm, source['geo'])
                        row.update(packet_bytes=len(packet), **info, field_encoding_seconds=time.perf_counter()-before)
                        if sum(info['fees'].values()) != len(packet):
                            raise ValueError('Complete paid fees')
                        if algorithm == 0 and body != (ROOT/original['body']).read_bytes():
                            raise ValueError('Saved-DP carrier changed quotient/remainder/body')
                        for key, raw, folder, suffix in (('packet', packet, 'packets', '.qf01'), ('body', body, 'bodies', '.body')):
                            target = out/folder/(name+suffix); target.write_bytes(raw)
                            row[key], row[key+'_sha256'] = str(target.relative_to(ROOT)), sha(target)
                        output = out/'decodes'/(name+'.npz')
                        worker_report = out/'workers'/(name+'.json')
                        argv = [sys.executable, str(ROOT/'controls/worker.py'), str(ROOT/row['packet']),
                                str(output), str(worker_report), '--queries', str(ROOT/'data/queries.npy')]
                        process = subprocess.run(argv, env=dict(os.environ, **ENVIRONMENT), cwd=ROOT,
                                                 capture_output=True, text=True, timeout=120)
                        for stream in ('stdout', 'stderr'):
                            (out/'workers'/(name+'.'+stream+'.log')).write_text(getattr(process, stream))
                        row.update(worker_argv=argv, worker_returncode=process.returncode)
                        if process.returncode:
                            raise ValueError('Source-free worker failed')
                        with np.load(output, allow_pickle=False) as bundle:
                            y, mask, zero = bundle['y'], bundle['mask'], bundle['zero_protect']
                        if not np.array_equal(y, field) or not np.array_equal(mask, source['mask']):
                            raise ValueError('Actual decoded field/mask')
                        if mode == 'zero-preserve' and (np.any(y[source['x'] == 0]) or not np.array_equal(zero, protected & ~mask)):
                            raise ValueError('Actual protected-zero contract')
                        error = integer_error(source['x'], y, source['mask'], mask)
                        maximum = int(independent_rectangle_max(y.astype(np.int64)-source['x']))
                        if maximum != error['all_rectangle_query_error_exact']:
                            raise ValueError('Independent rectangle algorithms disagree')
                        row['contracts'] = {str(e): contract(error, e) for e in (100, 1000)}
                        row['fine'] = int(np.count_nonzero(y.astype(np.int64) % step))
                        worker = json.loads(worker_report.read_text())
                        if worker['source_provided'] or len(worker['answers']) != 1024:
                            raise ValueError('Source-free common query interface')
                        for rectangle, answer in zip(q, worker['answers']):
                            a, b, c, d = map(int, rectangle)
                            count = int((~mask[a:b, c:d]).sum())
                            if answer != dict(sum=float(y[a:b, c:d].sum()) if count else None, count=count):
                                raise ValueError('Independent direct-slice query')
                        for key, target in (('output', output), ('worker_report', worker_report)):
                            row[key], row[key+'_sha256'] = str(target.relative_to(ROOT)), sha(target)
                        row.update(status='DECODED_AND_AUDITED', independent_maximum=maximum,
                                   direct_queries_checked=1024)
                    except Exception as error:
                        row.update(error=type(error).__name__+': '+str(error), traceback=traceback.format_exc())
                    row['attempt_wall_seconds'] = time.perf_counter()-began
                    rows.append(row)
                    write_json(out/'attempts'/(name+'.json'), row)
                    write_json(out/'ledger.json', rows)
                    write_json(out/'report.json', summary(rows, time.perf_counter()-started))
                    print(name, row['status'], row.get('packet_bytes'), row.get('error', ''), flush=True)
    verify_original()
    print(json.dumps(summary(rows, time.perf_counter()-started)['dp_necessity_gates'], indent=2), flush=True)
    if any(r['status'] != 'DECODED_AND_AUDITED' for r in rows):
        raise SystemExit(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.freeze:
        freeze()
    elif args.out is not None:
        run(args.out.resolve())
    else:
        parser.error('--freeze or --out is required')
