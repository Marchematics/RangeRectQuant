"""Frozen complete-file step minimization; original experiments are untouched."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import traceback

import numpy as np

from controls.rate_selected_step import encode_selected
from controls.viable_greedy import reconstruct
from research_common import ROOT, ColdDecoder, audit, legal, save, sha

OUT = ROOT/'results/step_selection_20261004'
BUDGETS = (100, 1000)
DIVISORS = (16, 12, 8, 6, 5, 4, 3, 2)


def descriptors():
    rows = []
    for product, manifest, cap in (
        ('built-area', 'data/heldout_20261001/manifest.json', 10000),
        ('water', 'data/water_20261002/manifest_v2.json', 100)):
        for source in json.loads((ROOT/manifest).read_text())['rows'][:4]:
            rows.append(dict(product=product, site=source['site'], source=source['source'],
                             source_sha256=source['source_sha256'], geo=source['geo'], cap=cap))
    return rows


def freeze():
    if (OUT/'preflight.json').exists():
        raise ValueError('Preflight already exists')
    names = [
        'controls/rate_selected_step.py', 'controls/viable_greedy.py',
        'controls/research_packet.py', 'controls/review_geometry.py',
        'experiments/run_step_selection.py', 'experiments/research_common.py',
        'experiments/research_decoder.py', 'tests/test_rate_selected_step.py',
        'docs/STEP_SELECTION_PROTOCOL_20261004.md',
        'data/heldout_20261001/manifest.json', 'data/water_20261002/manifest_v2.json']
    files = {name: sha(ROOT/name) for name in names}
    for source in descriptors():
        files[source['source']] = source['source_sha256']
    # Protect the unchanged article and the original scan measurements.
    protected = {}
    for folder in ('paper', 'results/review_revision_20261002/step'):
        for path in sorted((ROOT/folder).rglob('*')):
            if path.is_file() and path.suffix not in ('.pyc', '.nbc', '.nbi'):
                protected[str(path.relative_to(ROOT))] = sha(path)
    save(OUT/'preflight.json', dict(
        status='FROZEN_BEFORE_STEP_SELECTION', utc=datetime.now(timezone.utc).isoformat(),
        files=files, protected=protected, python=sys.executable,
        sources=descriptors(), budgets=list(BUDGETS), built_area_divisors=list(DIVISORS),
        water_step_domain=[1, 65536], expected_selections=16,
        expected_full_construction_trials=872, expected_candidate_lengths=524352,
        expected_cold_decodes=16, gpu_used=False))


def verify_frozen():
    preflight = json.loads((OUT/'preflight.json').read_text())
    for path, expected in dict(preflight['files'], **preflight['protected']).items():
        if sha(ROOT/path) != expected:
            raise ValueError('Frozen input changed: '+path)
    return preflight


def case(source, epsilon):
    folder = OUT/source['product']/source['site']/f'e{epsilon}'
    folder.mkdir(parents=True)
    decoder = ColdDecoder(folder/'decoder')
    started = time.perf_counter()
    try:
        with np.load(ROOT/source['source'], allow_pickle=False) as data:
            x, mask = data['raw'].astype(np.int64), data['mask'].astype(bool)
        x[mask] = 0
        if x.shape != (512, 512):
            raise ValueError('Frozen native shape changed')
        cap = source['cap']
        candidates = None if source['product'] == 'water' else [
            max(1, epsilon//d) for d in DIVISORS]
        blob, selected, detail = encode_selected(x, epsilon, cap, mask, mask,
                                                candidates=candidates, geo=source['geo'])
        path = folder/'selected.packet'; path.write_bytes(blob)
        y, m, p, info = decoder.decode(path)
        if not np.array_equal(y, selected) or info['source_provided']:
            raise ValueError('Cold decoder changed selected field or received source')
        a = audit(x, y, mask, m, mask, p, cap=cap)
        if not legal(a, epsilon):
            raise ValueError('Selected packet failed exact joint audit')
        default = max(1, epsilon//5)
        if source['product'] == 'water':
            default = min(cap, default)
        base = next(r for r in detail['rows'] if r['step'] == default)
        lengths = [(r['packet_bytes'], r['step']) for r in detail['rows']]
        tail = detail['large_step_equivalence']
        if tail:
            lengths.append((tail['best_bytes'], tail['best_step']))
        if (detail['selected_bytes'], detail['selected_step']) != min(lengths):
            raise ValueError('Complete-file argmin mismatch')
        if len(blob) > base['packet_bytes'] or info['meta']['step'] != detail['selected_step']:
            raise ValueError('No-regret or signalled step mismatch')
        row = dict(status='SELECTED_DECODED_AND_EXACTLY_AUDITED', product=source['product'],
                   site=source['site'], source=source['source'],
                   source_sha256=source['source_sha256'], epsilon=epsilon, pixels=x.size,
                   cap=cap, packet=str(path.relative_to(ROOT)), packet_sha256=sha(path),
                   default_step=default, default_bytes=base['packet_bytes'],
                   default_in_loop_seconds=base['construction_and_encoding_seconds'],
                   selected_step=detail['selected_step'], selected_bytes=len(blob),
                   reduction=1-len(blob)/base['packet_bytes'], audit=a, decoder=info,
                   selection=detail, total_case_seconds=time.perf_counter()-started)
        save(folder/'case.json', row)
        return row
    except Exception as error:
        row = dict(status='EXCEPTION', product=source['product'], site=source['site'], epsilon=epsilon,
                   error=type(error).__name__+': '+str(error), traceback=traceback.format_exc())
        save(folder/'case.json', row)
        return row
    finally:
        decoder.close()


def old_scan_reanalysis():
    rows = []
    for case_path in sorted((ROOT/'results/review_revision_20261002/step').glob('*/case.json')):
        old = json.loads(case_path.read_text())
        for epsilon in BUDGETS:
            candidates = [r for r in old['rows'] if r['configuration']['epsilon'] == epsilon]
            best = min(candidates, key=lambda r: (r['packet_bytes'], r['configuration']['quantization_step']))
            base = next(r for r in candidates if r['configuration']['divisor'] == 5)
            rows.append(dict(site=old['site'], split=old['split'], epsilon=epsilon,
                             default_bytes=base['packet_bytes'], best_bytes=best['packet_bytes'],
                             best_step=best['configuration']['quantization_step'],
                             best_divisor=best['configuration']['divisor'],
                             reduction=1-best['packet_bytes']/base['packet_bytes'],
                             all_legal=all(r['audit']['legal_at'][str(epsilon)] for r in candidates)))
    if len(rows) != 16:
        raise ValueError('Expected 128 original measurements')
    return dict(status='REANALYSIS_OF_PREVIOUSLY_SAVED_128_FILES', rows=rows,
                metadata_schema='original, including divisor; separate from new measurements')


def summary(cases, preflight):
    successful = [c for c in cases if c['status'] == 'SELECTED_DECODED_AND_EXACTLY_AUDITED']
    groups = []
    for product in ('built-area', 'water'):
        for epsilon in BUDGETS:
            rows = [r for r in successful if r['product'] == product and r['epsilon'] == epsilon]
            n = sum(r['pixels'] for r in rows)
            default = sum(r['default_bytes'] for r in rows)
            selected = sum(r['selected_bytes'] for r in rows)
            groups.append(dict(product=product, epsilon=epsilon, cases=len(rows),
                               default_bytes=default, selected_bytes=selected,
                               default_bpp=8*default/n if n else None,
                               selected_bpp=8*selected/n if n else None,
                               reduction=1-selected/default if default else None,
                               selected_steps=[r['selected_step'] for r in rows],
                               search_seconds=sum(r['selection']['elapsed_seconds'] for r in rows),
                               default_in_loop_seconds=sum(r['default_in_loop_seconds'] for r in rows)))
    total_trials = sum(r['selection']['full_construction_trials'] for r in successful)
    total_lengths = sum(r['selection']['candidate_count'] for r in successful)
    passed = (len(successful) == preflight['expected_selections']
              and total_trials == preflight['expected_full_construction_trials']
              and total_lengths == preflight['expected_candidate_lengths'])
    return dict(status='PASS_ALL_FROZEN_CASES' if passed else 'INCOMPLETE_OR_FAILED',
                selections=len(successful), exceptions=len(cases)-len(successful),
                cold_decodes=len(successful), exact_rectangle_audits=len(successful),
                full_construction_trials=total_trials, candidate_lengths=total_lengths,
                groups=groups, cases=cases, saved_scan_reanalysis=old_scan_reanalysis(),
                optimum_scope=dict(water='all 65536 transport-valid steps for the fixed constructor/coder',
                                   built_area='the eight predeclared steps for the fixed constructor/coder'),
                gpu_used=False, canonical_paper_changed=False)


def run():
    preflight = verify_frozen()
    if (OUT/'report.json').exists():
        raise ValueError('Refuse overwrite report')
    # Separate compilation from measured native-field search.
    reconstruct(np.zeros((2, 2), np.int64), 1, 1, 100)
    rows = []
    for source in preflight['sources']:
        for epsilon in BUDGETS:
            row = case(source, epsilon); rows.append(row)
            print(json.dumps({k: row.get(k) for k in (
                'product', 'site', 'epsilon', 'status', 'selected_step', 'reduction')}, allow_nan=False), flush=True)
    verify_frozen()
    result = summary(rows, preflight)
    save(OUT/'report.json', result)
    if result['status'] != 'PASS_ALL_FROZEN_CASES':
        raise RuntimeError('Failures retained; protocol completion criteria not met')


def replay():
    preflight = verify_frozen()
    original = json.loads((OUT/'report.json').read_text())
    folder = OUT/'replay'; folder.mkdir()
    decoder = ColdDecoder(folder/'decoder')
    try:
        for row in original['cases']:
            if row['status'] != 'SELECTED_DECODED_AND_EXACTLY_AUDITED':
                raise ValueError('Cannot replay an incomplete report')
            packet = ROOT/row['packet']
            if sha(packet) != row['packet_sha256']:
                raise ValueError('Selected packet changed')
            y, m, p, info = decoder.decode(packet)
            with np.load(ROOT/row['source'], allow_pickle=False) as data:
                x, mask = data['raw'].astype(np.int64), data['mask'].astype(bool)
            x[mask] = 0
            a = audit(x, y, mask, m, mask, p, cap=row['cap'])
            if a != row['audit'] or not legal(a, row['epsilon']) or info['source_provided']:
                raise ValueError('Replay audit changed')
        rebuilt = summary(original['cases'], preflight)
        if rebuilt != original:
            raise ValueError('Aggregate report does not match saved cases')
        save(folder/'validation.json', dict(status='PASS_16_SAVED_WINNERS', source_free_decodes=decoder.count,
                                          exact_rectangle_audits=decoder.count, frozen_inputs_unchanged=True,
                                          aggregates_identical=True))
    finally:
        decoder.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('freeze', 'run', 'replay'))
    args = parser.parse_args()
    {'freeze': freeze, 'run': run, 'replay': replay}[args.command]()
