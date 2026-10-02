"""Verify saved complete files and the instance-dependent review comparisons."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    revision=json.loads((ROOT/'results/review_revision_20261002/report.json').read_text())
    native=json.loads((ROOT/'results/review_dense_20261002/report.json').read_text())
    counts={};exact=0;sourcefree=0;packet_bytes=0
    for block,pattern in (
        ('representation','results/review_revision_20261002/representation/*/case.json'),
        ('step','results/review_revision_20261002/step/*/case.json'),
        ('hierarchy','results/review_revision_20261002/hierarchy/*/case.json'),
        ('native-density','results/review_dense_20261002/*/case.json')):
        cases=[json.loads(p.read_text()) for p in sorted(ROOT.glob(pattern))];n=0
        for case in cases:
            for row in case['rows']:
                assert row['status']=='DECODED_AND_AUDITED'
                packet=ROOT/row['packet'];n+=1;packet_bytes+=packet.stat().st_size
                assert packet.stat().st_size==row['packet_bytes']==sum(row['fees'].values())
                assert sha(packet)==row['packet_sha256']==row['decoder']['packet_sha256']
                assert row['decoder']['source_provided'] is False;sourcefree+=1
                audit=row['audit'];e=audit['max_abs_prefix_error'];error=audit['rectangle_error_exact']
                assert audit['rectangle_error_lower']==e and audit['rectangle_error_upper']==4*e
                for budget,legal in audit['legal_at'].items():
                    b=int(budget)
                    assert not(e<=b<4*e and error is None)
                    assert legal==bool(error<=b if error is not None else 4*e<=b)
                exact+=error is not None
                if block=='representation' and row['configuration']['layout']!='quotient-only':
                    assert row['decoder']['numerator_sha256']==row['original_y_sha256']
                if block=='hierarchy':assert audit['global_sum_error']==0
                if block=='step':
                    g=row['geometry'];assert g['fine']==g['missing_coarse_residue']+g['protected_fine']
                    assert g['fine']<=g['width_bound_fine']
                if block=='native-density':
                    assert row['native_encode_commands'] and row['decoder']['native_commands']
                    assert all(c['returncode']==0 for c in row['native_encode_commands']+row['decoder']['native_commands'])
        counts[block]=dict(cases=len(cases),complete_files=n)
    assert sourcefree==4232
    assert {k:v['complete_files'] for k,v in counts.items()}==dict(representation=1280,step=128,hierarchy=2400,**{'native-density':424})
    bindings=0
    for name in ('review_revision_preflight_20261002.json','review_dense_preflight_20261002.json'):
        p=ROOT/'integration/checks'/name;f=json.loads(p.read_text())
        for group in ('files','runtimes'):
            for path,h in f[group].items():assert sha(path)==h;bindings+=1
    # Keep the old scientific record and every failed engineering attempt.
    rejected=0
    for pattern in ('results/review_revision_20261002/dense/*/case.json','results/review_dense_environment_gate_20261002/*/case.json'):
        for p in ROOT.glob(pattern):
            for row in json.loads(p.read_text())['rows']:
                assert row['status']=='EXCEPTION';rejected+=1
    assert rejected==848
    for r in revision['blocks']['hierarchy']['comparisons']:
        assert r['strict_main_wins']==40
        assert r['main_bytes']==sum(p['main_bytes'] for p in r['pairs'])
        assert r['reference_bytes']==sum(p['new_reference_bytes'] for p in r['pairs'])
    assert all(p['old_reference_bytes']==p['new_reference_bytes'] for r in native['comparisons'] for p in r['pairs'])
    report=dict(status='PASS_ALL_REVIEW_FILES_AND_BINDINGS',counts=counts,complete_sourcefree_files=sourcefree,
                complete_packet_bytes=packet_bytes,rows_with_exact_rectangle_maximum=exact,
                frozen_binding_checks=bindings,retained_adapter_environment_failures=rejected,
                sourcefree_native_decodes=424,native_codec_exceptions=0,gpu_used=False)
    target=ROOT/'integration/checks/review_delivery_validation_20261002.json'
    target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
