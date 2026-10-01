"""Read-only hash/fee attribution of the frozen control, not new encoding."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / 'results/viable_greedy_20261001'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    outputs = [RESULT / 'attribution.json', RESULT / 'cases.csv']
    if any(p.exists() for p in outputs):
        raise SystemExit('Refusing to overwrite attribution')
    bindings = {}
    for name in ('preflight_20261001', 'viable_greedy_preflight_20261001'):
        frozen = read(ROOT / 'integration/checks' / (name + '.json'))
        count = 0
        for group in ('files', 'runtimes'):
            for key, expected in frozen[group].items():
                path = ROOT / key if group == 'files' else Path(key)
                if sha(path) != expected:
                    raise ValueError('Frozen binding: ' + key)
                count += 1
        bindings[name] = count
    supplied = read(ROOT / 'integration/IMPORT_MANIFEST.json')
    archive = ROOT / 'imports/LinewiseROI_Research_Plan_and_Probe_20261001.zip'
    if sha(archive) != supplied['archive_sha256'] or archive.stat().st_size != supplied['archive_bytes']:
        raise ValueError('Supplied archive')
    refs = read(ROOT / 'integration/REFERENCE_MANIFEST.json')
    historical = ROOT.parent / 'LinewiseROI'
    manifest = historical / 'integration/IMPORT_MANIFEST.json'
    if sha(manifest) != refs['previous_import_manifest_sha256']:
        raise ValueError('Historical manifest')
    preserved = {}
    for label, base, entries in (
        ('supplied', ROOT, supplied['files']),
        ('historical', historical, read(manifest)['files']),
        ('previous', ROOT, [dict(v, path=k) for k, v in refs['previous_files'].items()]),
    ):
        for row in entries:
            path = base / row['path']
            if path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
                raise ValueError('Preservation: ' + row['path'])
        preserved[label] = len(entries)
    rows = read(RESULT / 'ledger.json')
    if len(rows) != 32 or len({r['id'] for r in rows}) != 32:
        raise ValueError('Frozen matrix')
    old = {r['id']: r for r in read(ROOT / 'results/pilot_20261001/ledger.json')}
    artifact_count = 0
    csv_rows = []
    for row in rows:
        if row['status'] != 'DECODED_AND_AUDITED':
            raise ValueError('Incomplete control')
        for key in ('packet', 'body', 'output', 'worker_report'):
            if sha(ROOT / row[key]) != row[key + '_sha256']:
                raise ValueError('Artifact: ' + row['id'] + ':' + key)
            artifact_count += 1
        if row['packet_bytes'] != (ROOT / row['packet']).stat().st_size or sum(row['fees'].values()) != row['packet_bytes']:
            raise ValueError('Complete fees')
        if sum(row['body_detail'].values()) != row['fees']['body_bytes']:
            raise ValueError('Body fees')
        if row['algorithm_id'] == 0:
            prior = old[f"{row['site']}-q{row['step']}-{row['mode']}"]
            if (ROOT / row['body']).read_bytes() != (ROOT / prior['body']).read_bytes():
                raise ValueError('Original DP body changed')
        epsilon = 100 if row['step'] == 20 else 1000
        csv_rows.append(dict(id=row['id'], site=row['site'], epsilon=epsilon,
            mode=row['mode'], algorithm_id=row['algorithm_id'], packet_bytes=row['packet_bytes'],
            **row['fees'], **row['body_detail'], fine=row['fine'],
            roi_max=row['independent_maximum'],
            designated_verdict=row['contracts'][str(epsilon)]['status'],
            construction_seconds=row['construction_seconds']))
    groups = []
    report = read(RESULT / 'report.json')
    for group in report['groups']:
        selected = [r for r in csv_rows if r['epsilon'] == group['epsilon'] and r['mode'] == group['mode']]
        totals = {}
        for algorithm in (0, 1):
            cases = [r for r in selected if r['algorithm_id'] == algorithm]
            if len(cases) != 4 or any(r['designated_verdict'] != 'LEGAL' for r in cases):
                raise ValueError('Incomplete/legal paired group')
            totals[str(algorithm)] = {key: sum(r[key] for r in cases) for key in
                ('packet_bytes', 'body_bytes', 'config_bytes', 'quotient_bytes', 'remainder_bytes',
                 'source_zero_bitmap_bytes', 'fine')}
        dp, greedy = totals['0'], totals['1']
        if dp['packet_bytes'] != group['dp_bytes'] or greedy['packet_bytes'] != group['greedy_bytes']:
            raise ValueError('Report totals')
        prior_total = sum(r['strong_prior_bytes'] for r in refs['comparisons'] if r['epsilon'] == group['epsilon'])
        groups.append(dict(epsilon=group['epsilon'], mode=group['mode'], totals=totals,
            greedy_minus_dp={k: greedy[k] - dp[k] for k in dp},
            dp_reduction_from_greedy=1-dp['packet_bytes']/greedy['packet_bytes'],
            dp_fine_reduction_from_greedy=1-dp['fine']/greedy['fine'],
            named_strong_prior_bytes=prior_total,
            greedy_reduction_from_named_strong_prior=1-greedy['packet_bytes']/prior_total))
    if any(g['passed'] for g in report['dp_necessity_gates']):
        raise ValueError('Unexpected frozen necessity outcome')
    attribution = dict(status='PASS_SAVED_HASH_AND_COMPLETE_FEE_ATTRIBUTION',
        report_sha256=sha(RESULT / 'report.json'), frozen_bindings=bindings,
        artifact_sha_checks=artifact_count, preserved=preserved, groups=groups,
        optimizer_runs=0, codec_runs=0, new_sources=0, all_rectangle_algorithm_repeated=False,
        integrity_audit='unavailable; this saved-data check is not EXPERIMENT_AUDIT',
        necessity_claim_supported=False, novelty_established=False, sota_established=False)
    outputs[0].write_text(json.dumps(attribution, indent=2, allow_nan=False) + '\n')
    with outputs[1].open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(json.dumps(attribution, indent=2))


if __name__ == '__main__':
    main()
