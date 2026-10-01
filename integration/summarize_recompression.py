"""Read-only lineage, paid-rate and stabilization accounting of frozen resaves."""
from __future__ import annotations

from collections import Counter
import csv
import json

import numpy as np

from controls.field_packet import decode as decode_greedy
from range_rect_quant.packet import HEADER, BODY_HEADER, SETTINGS, decode as decode_dp
from run_pilot import ROOT, sha, sources, verify_preserved
from run_recompression_diagnostic import check_bindings, initial_cases, summarize

RESULT = ROOT / 'results/recompression_20261001'


def read(path):
    return json.loads(path.read_text())


def first_pass(rows, predicate):
    return next((row['pass'] for row in rows if predicate(row)), None)


def remainder_headroom():
    # This is an accounting bound for fixed quotient/config/mask bytes only.
    groups = read(ROOT / 'results/viable_greedy_20261001/attribution.json')['groups']
    return [dict(epsilon=group['epsilon'], algorithm=algorithm,
                 packet_bytes=group['totals'][key]['packet_bytes'],
                 remainder_bytes=group['totals'][key]['remainder_bytes'],
                 saving_if_entire_remainder_free=(
                     group['totals'][key]['remainder_bytes'] /
                     group['totals'][key]['packet_bytes']))
            for group in groups if group['mode'] == 'lossy'
            for key, algorithm in (('0', 'dp'), ('1', 'greedy'))]


def main():
    targets = [RESULT / 'attribution.json', RESULT / 'cases.csv', RESULT / 'chains.csv']
    if any(path.exists() for path in targets):
        raise SystemExit('Refusing to overwrite saved-data attribution')
    report = read(RESULT / 'report.json')
    rows = read(RESULT / 'ledger.json')
    if report['status'] != 'COMPLETE' or len(rows) != 120 or len({r['id'] for r in rows}) != 120:
        raise ValueError('Incomplete or duplicate frozen matrix')
    if summarize(rows, report['elapsed_seconds']) != report:
        raise ValueError('Frozen report regeneration')
    bindings = {name: check_bindings(read(ROOT / 'integration/checks' / (name + '.json')))
                for name in ('preflight_20261001', 'viable_greedy_preflight_20261001',
                             'recompression_preflight_20261001')}
    preserved = verify_preserved()
    records = {s['site']: s for s in sources()}
    base_rows = {(r['algorithm'], r['site'], r['step']): r for r in initial_cases()}
    rectangles = np.load(ROOT / 'data/queries.npy', allow_pickle=False)
    artifact_checks = input_checks = direct_queries = 0
    cases = []
    chains = []
    for key, base in base_rows.items():
        selected = sorted((r for r in rows if (r['algorithm'], r['site'], r['step']) == key),
                          key=lambda r: r['pass'])
        algorithm, site, step = key
        if [r['pass'] for r in selected] != list(range(2, 3 if algorithm == 'identity' else 9)):
            raise ValueError('Frozen chain generations')
        input_path, input_sha = base['output'], base['output_sha256']
        previous_packet = (ROOT / base['packet']).read_bytes()
        for row in selected:
            if row['status'] != 'DECODED_AND_AUDITED':
                raise ValueError('Failed frozen step')
            if row['input'] != input_path or row['input_sha256'] != input_sha:
                raise ValueError('Chain lineage')
            if sha(ROOT / input_path) != input_sha:
                raise ValueError('Actual previous field SHA')
            input_checks += 1
            for name in ('packet', 'body', 'output', 'worker_report'):
                if sha(ROOT / row[name]) != row[name + '_sha256']:
                    raise ValueError('Saved artifact SHA')
                artifact_checks += 1
            packet = (ROOT / row['packet']).read_bytes()
            magic, h, w, ml, cl, bl, _ = HEADER.unpack_from(packet)
            if magic != (b'QF01' if algorithm == 'greedy' else b'RQ01'):
                raise ValueError('Within-chain carrier')
            if sum(row['fees'].values()) != len(packet) or row['packet_bytes'] != len(packet):
                raise ValueError('Full paid size')
            expected_fees = dict(header_bytes=HEADER.size, checksum_bytes=32,
                                 mask_bytes=ml, config_bytes=cl, body_bytes=bl)
            if row['fees'] != expected_fees:
                raise ValueError('Actual segment fees')
            body = packet[HEADER.size + ml + cl:-32]
            lengths = BODY_HEADER.unpack_from(body)
            detail = row['body_detail']
            if (body != (ROOT / row['body']).read_bytes() or
                    lengths != tuple(detail[k] for k in ('quotient_bytes', 'remainder_bytes',
                                                         'source_zero_bitmap_bytes')) or
                    BODY_HEADER.size + sum(lengths) != bl):
                raise ValueError('Actual paid body')
            y, mask, meta, protected = (decode_greedy if algorithm == 'greedy' else decode_dp)(packet)
            with np.load(ROOT / row['output'], allow_pickle=False) as saved:
                for field, value in (('y', y), ('mask', mask), ('zero_protect', protected)):
                    np.testing.assert_array_equal(saved[field], value)
            source = records[site]
            if row['original_source_sha256'] != source['source_sha256'] or meta['geo'] != source['geo']:
                raise ValueError('Source/geospatial provenance')
            np.testing.assert_array_equal(mask, source['mask'])
            if y.shape != (h, w) or protected.any():
                raise ValueError('Frozen field shape/default protection')
            with np.load(ROOT / input_path, allow_pickle=False) as previous:
                local = y.astype(np.int64) - previous['y'].astype(np.int64)
            changed = int(np.count_nonzero(local))
            prefix = int(np.abs(local.cumsum(0).cumsum(1)).max())
            fine = int(np.count_nonzero(y.astype(np.int64) % step))
            if (changed != row['changed_from_previous'] or prefix != row['local_max_abs_prefix'] or
                    fine != row['fine'] or prefix > SETTINGS[step][1]):
                raise ValueError('Field stabilization/local-prefix counts')
            worker = read(ROOT / row['worker_report'])
            if (worker['source_provided'] or worker['prefix_state_provided'] or
                    row['worker_returncode'] != 0 or len(worker['answers']) != 1024):
                raise ValueError('Saved source-free query service')
            for i, rectangle in enumerate(rectangles):
                a, b, c, d = map(int, rectangle)
                n = int((~mask[a:b, c:d]).sum())
                answer = dict(sum=float(y[a:b, c:d].sum()) if n else None, count=n)
                if worker['answers'][i] != answer:
                    raise ValueError('Direct slice query')
                direct_queries += 1
            cases.append(dict(id=row['id'], algorithm=algorithm, site=site, epsilon=SETTINGS[step][0],
                              generation=row['pass'], packet_bytes=len(packet),
                              **expected_fees, quotient_bytes=lengths[0], remainder_bytes=lengths[1],
                              fine=fine, changed_from_previous=changed,
                              identical_packet_to_previous=packet == previous_packet,
                              local_maximum=row['local_maximum'], cumulative_maximum=row['cumulative_maximum']))
            input_path, input_sha, previous_packet = row['output'], row['output_sha256'], packet
        chain_cases = [r for r in cases if (r['algorithm'], r['site'], r['epsilon']) ==
                       (algorithm, site, SETTINGS[step][0])]
        final = selected[-1]
        chains.append(dict(algorithm=algorithm, site=site, epsilon=SETTINGS[step][0],
                           initial_packet_bytes=base['packet_bytes'], final_packet_bytes=final['packet_bytes'],
                           additional_paid_saving=1 - final['packet_bytes'] / base['packet_bytes'],
                           first_cumulative_violation=first_pass(selected, lambda r: r['cumulative_maximum'] > SETTINGS[step][0]),
                           first_all_coarse=first_pass(selected, lambda r: r['fine'] == 0),
                           first_unchanged_field=first_pass(selected, lambda r: r['changed_from_previous'] == 0),
                           first_identical_packet=next((r['generation'] for r in chain_cases
                                                       if r['identical_packet_to_previous']), None),
                           final_cumulative_maximum=final['cumulative_maximum'],
                           final_error_ratio=final['cumulative_maximum'] / SETTINGS[step][0],
                           final_fine=final['fine']))
    groups = []
    for algorithm in ('dp', 'greedy', 'identity'):
        for epsilon in (100, 1000):
            selected = [r for r in chains if r['algorithm'] == algorithm and r['epsilon'] == epsilon]
            initial = sum(r['initial_packet_bytes'] for r in selected)
            final = sum(r['final_packet_bytes'] for r in selected)
            groups.append(dict(algorithm=algorithm, epsilon=epsilon, initial_paid_bytes=initial,
                               final_paid_bytes=final, additional_paid_saving=1 - final / initial,
                               final_error_ratio_min=min(r['final_error_ratio'] for r in selected),
                               final_error_ratio_max=max(r['final_error_ratio'] for r in selected)))
    attribution = dict(status='PASS_SAVED_HASH_LINEAGE_AND_PAID_ACCOUNTING',
                       launch_commit=read(RESULT / 'launch.json')['commit'],
                       original_report_sha256=sha(RESULT / 'report.json'),
                       frozen_bindings=bindings, preserved=preserved,
                       artifact_sha_checks=artifact_checks, chain_input_sha_checks=input_checks,
                       in_process_packet_reads=len(cases), direct_queries_checked=direct_queries,
                       local_verdicts=dict(Counter('LEGAL' if r['local_maximum'] <= r['epsilon'] else 'ILLEGAL' for r in cases)),
                       cumulative_verdicts=dict(Counter('LEGAL' if r['cumulative_maximum'] <= r['epsilon'] else 'ILLEGAL' for r in cases)),
                       groups=groups, chains=chains, fixed_quotient_remainder_headroom=remainder_headroom(),
                       optimizer_runs=0, encoder_runs=0, fresh_worker_runs=0,
                       all_rectangle_algorithm_repeated=False,
                       integrity_status='unavailable; not a standardized EXPERIMENT_AUDIT',
                       novelty_established=False, sota_established=False)
    targets[0].write_text(json.dumps(attribution, indent=2, allow_nan=False) + '\n')
    for path, entries in ((targets[1], cases), (targets[2], chains)):
        with path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(entries[0]))
            writer.writeheader(); writer.writerows(entries)
    print(json.dumps({k: v for k, v in attribution.items() if k != 'chains'}, indent=2))


if __name__ == '__main__':
    main()
