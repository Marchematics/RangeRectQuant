"""Fixed new-geography paid comparison; lightweight construction is primary."""
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

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT.parent / 'LinewiseROI'
sys.path.append(str(LEGACY / 'experiments'))
from built_area_discrete_packet import encode as encode_baseline, grid
from built_area_fiber_packet import encode as encode_fiber
from built_area_integer_metrics import integer_error, contract
from range_rect_quant.packet import encode as encode_dp, SETTINGS
from controls.field_packet import encode as encode_greedy
from controls.viable_greedy import reconstruct
from run_pilot import sha, write_json, git, verify_preserved

PREFLIGHT = ROOT / 'integration/checks/heldout_experiment_preflight_20261001.json'
MANIFEST = ROOT / 'data/heldout_20261001/manifest.json'
NATIVE_PREFLIGHT = LEGACY / 'integration/checks/built_area_discrete_preflight_20261001.json'


def configurations():
    return ([dict(family='baseline', config=c) for c in grid()] +
            [dict(family='fiber', mode=m) for m in (0, 25, 250)] +
            [dict(family=family, step=q) for family in ('dp', 'greedy') for q in (20, 200)])


def read(path):
    return json.loads(path.read_text())


def check_bindings(frozen):
    for group in ('files', 'runtimes'):
        for name, expected in frozen[group].items():
            if sha(ROOT / name if group == 'files' else Path(name)) != expected:
                raise ValueError('Frozen heldout binding: ' + name)


def freeze():
    if PREFLIGHT.exists():
        raise SystemExit('Refuse overwrite heldout experiment freeze')
    manifest = read(MANIFEST)
    if manifest['status'] != 'PASS_FOUR_NEW_NATIVE_SOURCES':
        raise ValueError('Complete new geography required')
    old = read(ROOT / 'integration/checks/recompression_preflight_20261001.json')
    check_bindings(old); verify_preserved()
    files, runtimes = dict(old['files']), dict(old['runtimes'])
    native = read(NATIVE_PREFLIGHT)
    for name, expected in native['bindings_sha256'].items():
        path = LEGACY / name
        if sha(path) != expected:
            raise ValueError('Unchanged external baseline source')
        files[str(path)] = expected
    for name, expected in native['runtime_sha256'].items():
        if sha(Path(name)) != expected:
            raise ValueError('External baseline runtime')
        runtimes[name] = expected
    paths = [Path(__file__), MANIFEST, NATIVE_PREFLIGHT,
             ROOT / 'docs/HOLDOUT_PROTOCOL_20261001.md',
             ROOT / 'integration/heldout_assets_20261001.json',
             ROOT / 'tests/test_heldout.py', ROOT / 'integration/checks/heldout_tests_20261001.log',
             LEGACY / 'experiments/built_area_fiber_packet.py',
             LEGACY / 'experiments/built_area_fiber_worker.py']
    for row in manifest['rows']:
        path = ROOT / row['source']
        if sha(path) != row['source_sha256']:
            raise ValueError('New source hash')
        paths.append(path)
    for path in paths:
        files[str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)] = sha(path)
    write_json(PREFLIGHT, dict(status='FROZEN_BEFORE_NEW_GEOGRAPHY_ENCODING', files=files,
                              runtimes=runtimes, environment=native['environment'],
                              configurations=configurations(), planned_packets=180,
                              source_manifest_sha256=sha(MANIFEST),
                              no_new_geography_encoded=True, main_family='greedy'))


def summarize(rows, elapsed):
    sites = [r['site'] for r in read(MANIFEST)['rows']]
    comparisons, gates = [], []
    for epsilon, step in ((100, 20), (1000, 200)):
        pairs = []
        for site in sites:
            group = [r for r in rows if r['site'] == site]
            legal = [r for r in group if r['configuration']['family'] in ('baseline', 'fiber') and
                     r.get('contracts', {}).get(str(epsilon), {}).get('status') == 'LEGAL']
            baseline = min(legal, key=lambda r: (r['packet_bytes'], r['id'])) if legal else None
            candidates = [r for r in group if r['configuration'] == dict(family='greedy', step=step)]
            candidate = candidates[0] if len(candidates) == 1 else None
            valid = bool(candidate and candidate['status'] == 'DECODED_AND_AUDITED' and
                         candidate['contracts'][str(epsilon)]['status'] == 'LEGAL' and
                         candidate['contracts'][str(epsilon)]['changed_values'] > 0)
            pair = dict(site=site, epsilon=epsilon, baseline_id=baseline['id'] if baseline else None,
                        baseline_bytes=baseline['packet_bytes'] if baseline else None,
                        main_bytes=candidate.get('packet_bytes') if candidate else None,
                        main_legal_nontrivial=valid)
            comparisons.append(pair); pairs.append(pair)
        complete = len(rows) == 180
        valid = complete and all(p['main_legal_nontrivial'] and p['baseline_bytes'] for p in pairs)
        previous = sum(p['baseline_bytes'] or 0 for p in pairs)
        current = sum(p['main_bytes'] or 0 for p in pairs)
        wins = sum(p['main_legal_nontrivial'] and p['baseline_bytes'] is not None and
                   p['main_bytes'] < p['baseline_bytes'] for p in pairs)
        expansion = max((p['main_bytes'] / p['baseline_bytes'] - 1 for p in pairs
                         if p['main_bytes'] is not None and p['baseline_bytes']), default=None)
        gain = 1 - current / previous if valid else None
        gates.append(dict(epsilon=epsilon, complete=complete, all_legal_nontrivial=bool(valid),
                          strict_wins=wins, baseline_bytes=previous, main_bytes=current,
                          reduction_fraction=gain, maximum_source_expansion_fraction=expansion,
                          passed=bool(valid and wins >= 3 and gain >= .10 and expansion <= .05)))
    verdicts = Counter(c['status'] for r in rows for c in r.get('contracts', {}).values())
    return dict(status='COMPLETE_FIXED_NEW_GEOGRAPHY_MATRIX' if len(rows) == 180 else 'PARTIAL',
                attempted_packets=len(rows), sourcefree_decodes=sum(r['status'] == 'DECODED_AND_AUDITED' for r in rows),
                exception_packets=sum(r['status'] == 'EXCEPTION' for r in rows),
                budget_verdicts=dict(verdicts), gates=gates, comparisons=comparisons,
                elapsed_seconds=elapsed, main_family='greedy', gpu_used=False,
                fixed_new_geography=True, product_cross_domain=False, broad_codec_sota_established=False)


def run(out):
    if out.exists() or not out.is_relative_to(ROOT / 'results'):
        raise SystemExit('Fresh result directory')
    if git('status', '--porcelain') or git('ls-remote', 'origin', 'refs/heads/main').split()[0] != git('rev-parse', 'HEAD'):
        raise SystemExit('Need clean pushed tree')
    frozen = read(PREFLIGHT); check_bindings(frozen); verify_preserved()
    if frozen['configurations'] != configurations():
        raise ValueError('Fixed baseline/method matrix')
    os.environ.update(frozen['environment'])
    environment = dict(os.environ, PYTHONPATH=os.pathsep.join(map(str, (ROOT, ROOT / 'src', ROOT / 'experiments', LEGACY / 'experiments'))))
    queries = np.load(ROOT / 'data/queries.npy', allow_pickle=False)
    manifest = read(MANIFEST)
    out.mkdir(parents=True)
    for name in ('packets', 'bodies', 'decodes', 'workers', 'attempts', 'native'):
        (out / name).mkdir()
    write_json(out / 'launch.json', dict(commit=git('rev-parse', 'HEAD'), clean_pushed_tree=True,
                                        preflight_sha256=sha(PREFLIGHT), source_manifest_sha256=sha(MANIFEST),
                                        environment=environment, started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
    rows = []; started = time.perf_counter()
    for source in manifest['rows']:
        with np.load(ROOT / source['source'], allow_pickle=False) as bundle:
            raw, mask = bundle['raw'], bundle['mask']
        x = raw.astype(np.int64); x[mask] = 0
        for index, cfg in enumerate(configurations()):
            if time.perf_counter() - started > 1800:
                raise TimeoutError('Fixed matrix limit; partial evidence retained')
            stem = f"{source['site']}-{index:02d}-{cfg['family']}"
            row = dict(id=stem, site=source['site'], configuration=cfg, status='EXCEPTION',
                       source=source['source'], source_sha256=source['source_sha256'])
            body_path = out / 'bodies' / (stem + '.body')
            commands = []; before = time.perf_counter()
            try:
                if cfg['family'] == 'baseline':
                    packet, info = encode_baseline(x, mask, cfg['config'], source['geo'], body_path,
                                                   commands, out / 'native' / stem / 'encoder')
                    body = body_path.read_bytes()
                    fees = {k: v for k, v in info.items() if k.endswith('_bytes')}
                    worker = LEGACY / 'experiments/built_area_discrete_worker.py'
                elif cfg['family'] == 'fiber':
                    packet, body, info = encode_fiber(x, mask, cfg['mode'], source['geo'])
                    fees = {k: v for k, v in info.items() if k.endswith('_bytes')}
                    worker = LEGACY / 'experiments/built_area_fiber_worker.py'
                elif cfg['family'] == 'dp':
                    packet, body, info = encode_dp(x, mask, cfg['step'], 'lossy', source['geo'])
                    fees = info['fees']; worker = ROOT / 'experiments/worker.py'
                else:
                    y, mechanism = reconstruct(x, SETTINGS[cfg['step']][1], cfg['step'], 10000, mask)
                    packet, body, info = encode_greedy(x, y, mask, cfg['step'], 'lossy', 1, source['geo'])
                    info['quantizer'] = mechanism; fees = info['fees']; worker = ROOT / 'controls/worker.py'
                if len(packet) != sum(fees.values()):
                    raise ValueError('Complete paid fees')
                row.update(packet_bytes=len(packet), fees=fees, encode_seconds=time.perf_counter() - before,
                           encoder_info=info, native_commands=commands)
                for name, value, folder, suffix in (('packet', packet, 'packets', '.packet'), ('body', body, 'bodies', '.body')):
                    path = out / folder / (stem + suffix)
                    if name == 'body' and path.exists():
                        if path.read_bytes() != value:
                            raise ValueError('Baseline body identity')
                    else:
                        path.write_bytes(value)
                    row[name], row[name + '_sha256'] = str(path.relative_to(ROOT)), sha(path)
                decoded, worker_report = out / 'decodes' / (stem + '.npz'), out / 'workers' / (stem + '.json')
                argv = [sys.executable, str(worker), str(ROOT / row['packet']), str(decoded), str(worker_report),
                        '--queries', str(ROOT / 'data/queries.npy')]
                if cfg['family'] == 'baseline':
                    argv += ['--native-evidence', str(out / 'native' / stem / 'decoder')]
                process = subprocess.run(argv, cwd=ROOT, env=environment, capture_output=True, text=True, timeout=120)
                row.update(worker_argv=argv, worker_returncode=process.returncode)
                for suffix, text in (('stdout', process.stdout), ('stderr', process.stderr)):
                    (out / 'workers' / (stem + '.' + suffix + '.log')).write_text(text)
                if process.returncode:
                    raise ValueError('Source-free worker failed')
                with np.load(decoded, allow_pickle=False) as bundle:
                    y, decoded_mask = bundle['y'], bundle['mask']
                if y.dtype != np.float64 or decoded_mask.dtype != bool or y.shape != x.shape:
                    raise ValueError('Full decoded field type/shape')
                worker_result = read(worker_report)
                if worker_result['source_provided'] or worker_result['meta']['geo'] != source['geo']:
                    raise ValueError('Source-free geo service')
                error = integer_error(x, y, mask, decoded_mask)
                row['contracts'] = {str(e): contract(error, e) for e in (100, 1000)}
                if len(worker_result['answers']) != len(queries):
                    raise ValueError('Full query list')
                for i, rectangle in enumerate(queries):
                    a, b, c, d = map(int, rectangle); n = int((~decoded_mask[a:b, c:d]).sum())
                    if worker_result['answers'][i] != dict(sum=float(y[a:b, c:d].sum()) if n else None, count=n):
                        raise ValueError('Direct query')
                row['direct_queries_checked'] = len(queries)
                if cfg['family'] in ('dp', 'greedy'):
                    row['fine'] = int(np.count_nonzero(y.astype(np.int64) % cfg['step']))
                for name, path in (('output', decoded), ('worker_report', worker_report)):
                    row[name], row[name + '_sha256'] = str(path.relative_to(ROOT)), sha(path)
                row['status'] = 'DECODED_AND_AUDITED'
            except Exception:
                row.update(exception=traceback.format_exc(), native_commands=commands)
            rows.append(row)
            write_json(out / 'attempts' / (stem + '.json'), row)
            write_json(out / 'ledger.json', rows)
            write_json(out / 'report.json', summarize(rows, time.perf_counter() - started))
            print(stem, row['status'], row.get('packet_bytes'), flush=True)
    check_bindings(frozen); verify_preserved()
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
