"""Saved paid-rate attribution and coverage; no codecs or optimizers run."""
from __future__ import annotations

import csv
import json

from run_pilot import ROOT, sha, verify_preserved, write_json
from run_heldout import check_bindings, summarize

RESULT = ROOT / 'results/heldout_20261001'


def main():
    targets = [RESULT / 'attribution.json', RESULT / 'cases.csv']
    if any(path.exists() for path in targets):
        raise SystemExit('Refuse overwrite heldout attribution')
    rows = json.loads((RESULT / 'ledger.json').read_text())
    report = json.loads((RESULT / 'report.json').read_text())
    if len(rows) != 180 or len({r['id'] for r in rows}) != 180:
        raise ValueError('Fixed matrix coverage')
    if summarize(rows, report['elapsed_seconds']) != report:
        raise ValueError('Heldout report regeneration')
    frozen = json.loads((ROOT / 'integration/checks/heldout_experiment_preflight_20261001.json').read_text())
    check_bindings(frozen); preserved = verify_preserved()
    artifacts = 0; cases = []
    for row in rows:
        if row['status'] != 'DECODED_AND_AUDITED':
            raise ValueError('Incomplete actual stream')
        for key in ('packet', 'body', 'output', 'worker_report'):
            if sha(ROOT / row[key]) != row[key + '_sha256']:
                raise ValueError('Saved artifact SHA')
            artifacts += 1
        if ((ROOT / row['packet']).stat().st_size != row['packet_bytes'] or
                sum(row['fees'].values()) != row['packet_bytes'] or
                row['fees']['body_bytes'] != (ROOT / row['body']).stat().st_size):
            raise ValueError('Complete actual fees')
        cfg = row['configuration']
        cases.append(dict(id=row['id'], site=row['site'], family=cfg['family'],
                          backend=cfg.get('config', {}).get('backend', cfg['family']),
                          step=cfg.get('step'), mode=cfg.get('mode'),
                          packet_bytes=row['packet_bytes'], **row['fees'],
                          fine=row.get('fine'), encode_seconds=row['encode_seconds'],
                          changed=row['contracts']['100']['changed_values'],
                          rectangle_max=row['contracts']['100']['all_rectangle_query_error_exact'],
                          epsilon100=row['contracts']['100']['status'],
                          epsilon1000=row['contracts']['1000']['status']))
    coverage = []
    for epsilon in (100, 1000):
        for backend in sorted({r['backend'] for r in cases}):
            selected = [r for r in cases if r['backend'] == backend]
            legal = [r for r in selected if r[f'epsilon{epsilon}'] == 'LEGAL']
            coverage.append(dict(backend=backend, epsilon=epsilon, attempts=len(selected),
                                 legal=len(legal), nontrivial_legal=sum(r['changed'] > 0 for r in legal)))
    mechanism = []
    for family in ('dp', 'greedy'):
        for step, epsilon in ((20, 100), (200, 1000)):
            selected = [r for r in cases if r['family'] == family and r['step'] == step]
            mechanism.append(dict(family=family, epsilon=epsilon,
                                  carrier='RQ01' if family == 'dp' else 'QF01',
                                  paid_bytes=sum(r['packet_bytes'] for r in selected),
                                  fine=sum(r['fine'] for r in selected),
                                  changed=sum(r['changed'] for r in selected),
                                  worst_rectangle_max=max(r['rectangle_max'] for r in selected)))
    attribution = dict(status='PASS_SAVED_HELDOUT_HASH_FEES_AND_REPORT',
                       report_sha256=sha(RESULT / 'report.json'), artifact_sha_checks=artifacts,
                       frozen_files=len(frozen['files']), frozen_runtimes=len(frozen['runtimes']),
                       preserved=preserved, coverage=coverage, mechanism=mechanism,
                       main_gates=report['gates'], optimizer_runs=0, codec_runs=0,
                       independent_geometry_repeated=False,
                       dp_greedy_carriers_matched=False,
                       broad_codec_sota_established=False)
    write_json(targets[0], attribution)
    with targets[1].open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cases[0]))
        writer.writeheader(); writer.writerows(cases)
    print(json.dumps(attribution, indent=2))


if __name__ == '__main__':
    main()
