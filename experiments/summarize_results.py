"""Descriptive tables from the frozen ledger; no optimizer or selection."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def summarize(source: Path) -> None:
    ledger_path = source / 'ledger.json'
    report_path = source / 'report.json'
    outputs = [source / 'attribution.json', source / 'cases.csv']
    if any(p.exists() for p in outputs):
        raise SystemExit('Refusing to overwrite derived tables')
    rows = json.loads(ledger_path.read_text())
    report = json.loads(report_path.read_text())
    if len(rows) != 24 or len({r['id'] for r in rows}) != 24:
        raise ValueError('Expected the frozen 24 distinct services')
    cases, budgets = [], []
    for row in rows:
        if row['status'] != 'DECODED_AND_AUDITED':
            raise ValueError('Incomplete saved service')
        fees, body = row['fees'], row['body_detail']
        if sum(fees.values()) != row['packet_bytes']:
            raise ValueError('Incomplete fee accounting')
        if (body['body_header_bytes'] + body['quotient_bytes'] +
                body['remainder_bytes'] + body['source_zero_bitmap_bytes']) != fees['body_bytes']:
            raise ValueError('Body accounting')
        epsilon = 100 if row['step'] == 20 else 1000
        case = dict(id=row['id'], site=row['site'], epsilon=epsilon,
                    step=row['step'], mode=row['mode'], packet_bytes=row['packet_bytes'],
                    legal=row['contracts'][str(epsilon)]['status'] == 'LEGAL',
                    all_rectangle_maximum=row['contracts'][str(epsilon)]['all_rectangle_query_error_exact'],
                    fine=row['quantizer']['off_lattice'], changed=row['quantizer']['changed'],
                    zero_to_positive=body['changed_source_valid_zeros'])
        case.update(fees)
        case.update({k: body[k] for k in ('quotient_bytes', 'remainder_bytes',
                                         'source_zero_bitmap_bytes')})
        cases.append(case)
    for epsilon, step in ((100, 20), (1000, 200)):
        group = [r for r in rows if r['step'] == step]
        modes = {}
        for mode in ('lossy', 'zero-preserve', 'identity'):
            services = [r for r in group if r['mode'] == mode]
            if len(services) != 4 or len({r['site'] for r in services}) != 4:
                raise ValueError('Missing fixed site/mode')
            modes[mode] = dict(
                packet_bytes=sum(r['packet_bytes'] for r in services),
                fine=sum(r['quantizer']['off_lattice'] for r in services),
                changed=sum(r['quantizer']['changed'] for r in services),
                zero_to_positive=sum(r['body_detail']['changed_source_valid_zeros'] for r in services),
                all_legal=all(r['contracts'][str(epsilon)]['status'] == 'LEGAL' for r in services))
        gate = report['gates'][f'{epsilon}:strong_prior_including_conditional_haar']
        lossy = modes['lossy']['packet_bytes']
        if lossy != gate['candidate_bytes']:
            raise ValueError('Derived total differs from frozen report')
        for mode in modes.values():
            mode['reduction_from_strong_prior'] = 1 - mode['packet_bytes'] / gate['baseline_bytes']
            mode['fine_fraction_of_1048576'] = mode['fine'] / 1048576
        budgets.append(dict(
            epsilon=epsilon, step=step, strong_prior_bytes=gate['baseline_bytes'], modes=modes,
            lossy_reduction_from_same_format_identity=1-lossy/modes['identity']['packet_bytes'],
            source_zero_preservation_overhead_over_lossy=modes['zero-preserve']['packet_bytes']/lossy-1))
    description = dict(
        status='PASS_SAVED_TABLE_DERIVATION', budgets=budgets,
        ledger_sha256=hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
        report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        descriptive_after_pilot=True, new_optimizer_runs=0, new_sources=0)
    outputs[0].write_text(json.dumps(description, indent=2, allow_nan=False)+'\n')
    with outputs[1].open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cases[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(cases)
    print('PASS 24 fee-checked saved cases, two fixed attribution groups')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    summarize(parser.parse_args().source)
