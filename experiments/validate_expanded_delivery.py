"""Verify saved complete files, accounting, fixed inputs and reported frontiers."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from research_common import ROOT, legal, save, sha


def verify_row(row):
    if row['status'] != 'DECODED_AND_AUDITED':
        return False
    blob = (ROOT / row['packet']).read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if (len(blob) != row['packet_bytes'] or digest != row['packet_sha256']
            or hashlib.sha256(blob[:-32]).digest() != blob[-32:]
            or sum(row['fees'].values()) != len(blob)
            or row['decoder']['source_provided'] is not False):
        raise ValueError('Saved-file verification: ' + row['id'])
    if 'packet_sha256' in row['decoder'] and row['decoder']['packet_sha256'] != digest:
        raise ValueError('Decoder did not receive saved file: ' + row['id'])
    for budget, recorded in row['legal_at'].items():
        if legal(row['audit'], int(budget)) != recorded:
            raise ValueError('Eligibility drift: ' + row['id'])
    return True


def run():
    from run_pilot import verify_preserved
    preserved = verify_preserved()
    frozen = json.loads((ROOT / 'integration/checks/expanded_encoding_preflight_20261002_v2.json').read_text())
    checked = 0
    for group in ('files', 'runtimes'):
        for path, expected in frozen[group].items():
            if sha(path) != expected:
                raise ValueError('Frozen dependency changed: ' + path)
            checked += 1
    water_freeze = json.loads((ROOT / 'integration/checks/water_encoding_preflight_20261002.json').read_text())
    for path, expected in water_freeze['files'].items():
        if sha(path) != expected:
            raise ValueError('Frozen percentage dependency changed: ' + path)
        checked += 1
    base = ROOT / 'results/expanded_frontier_20261002'
    report = json.loads((base / 'report.json').read_text())
    if report['status'] != 'COMPLETE_FIXED_40_LOCATION_MATRIX':
        raise ValueError('Incomplete geographic matrix')
    cases = [json.loads(p.read_text()) for p in sorted(base.glob('*/ledger.json'))]
    if len(cases) != 120 or any(len(c['rows']) != 55 for c in cases):
        raise ValueError('Fixed matrix count')
    for c in cases:
        if sha(ROOT / c['source']) != c['source_sha256']:
            raise ValueError('Source changed: ' + c['source'])
    rows = [r for c in cases for r in c['rows']]
    main = [r for r in rows if r['configuration']['family'] == 'RangeRectQuant']
    if len(main) != 960 or any(not r['legal_at'][str(r['configuration']['epsilon'])] for r in main):
        raise ValueError('A main file fails its requested guarantee')
    if any(r['mechanism']['unprotected_fine'] and
           r['mechanism']['unprotected_fine'] > r['mechanism']['unprotected_narrow'] for r in main):
        raise ValueError('Fine interval certificate')
    # Recompute every external-best point from eligible complete files.
    for point in report['frontier']:
        selected = [c for c in cases if c['size'] == point['size']]
        external = []
        for case in selected:
            eligible = [r for r in case['rows'] if r['configuration']['family'] != 'RangeRectQuant'
                        and r['status'] == 'DECODED_AND_AUDITED' and r['legal_at'][str(point['epsilon'])]]
            external.append(min(eligible, key=lambda r: (r['packet_bytes'], r['id'])))
        total = sum(r['packet_bytes'] for r in external)
        if total != point['totals_bytes']['external-best']:
            raise ValueError('Reference selection drift')
    groups = {'frontier': rows}
    for group, directory in (('closest', 'closest_mechanism'), ('protected', 'protected_sweep'),
                             ('water', 'water_frontier')):
        groups[group] = json.loads((ROOT / f'results/{directory}_20261002/ledger.json').read_text())['rows']
    expected = {'frontier': 6600, 'closest': 56, 'protected': 40, 'water': 392}
    result = {}
    for name, records in groups.items():
        if len(records) != expected[name]:
            raise ValueError('Attempt count: ' + name)
        decoded = sum(verify_row(r) for r in records)
        delivered = {str(ROOT / r['packet']) for r in records if r['status'] == 'DECODED_AND_AUDITED'}
        actual = {str(p) for p in (ROOT / f'.aris/evidence/expanded_20261002/{name}').rglob('*.packet')}
        if actual != delivered:
            raise ValueError('Unaccounted or missing packet: ' + name)
        result[name] = dict(attempts=len(records), verified_files=decoded,
                            exceptions=len(records)-decoded, bytes=sum(r['packet_bytes'] for r in records if r['status']=='DECODED_AND_AUDITED'))
    replay = json.loads((ROOT / 'results/native_replay_verification_20261002/ledger.json').read_text())['rows']
    if len(replay) != 5 or not all(verify_row(row) for row in replay):
        raise ValueError('Replay file verification')
    if any(any(r['improves_original_reference'].values()) for r in replay):
        raise ValueError('Replay changes a reference; update comparison evidence')
    save(ROOT / 'integration/checks/expanded_delivery_validation_20261002.json',
         dict(status='PASS_SAVED_FILES_AND_FIXED_INPUTS',groups=result,
              frozen_bindings_verified=checked,main_files_joint_valid=960,
              reference_points_recomputed=24,source_free=True,gpu_used=False,
              additional_native_replay_files=5,replay_changes_reference=False,preserved=preserved,
              scope='checks saved bytes and recorded exact audits; does not replace source-free decode logs'))


if __name__ == '__main__':
    run()
