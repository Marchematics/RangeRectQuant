"""Replay frozen step evidence after an explicitly requested manuscript edit.

The paper is not a computational input. Source/code/previous scan hashes stay
strictly checked; changes to the prose are listed rather than silently ignored.
The experiment's original pre-edit replay is retained alongside this receipt.
"""
import argparse
import json
from pathlib import Path
import tempfile

import numpy as np

from research_common import ROOT, ColdDecoder, audit, legal, save, sha
from run_step_selection import OUT, summary


def main(output=None):
    preflight = json.loads((OUT/'preflight.json').read_text())
    for path, expected in preflight['files'].items():
        if sha(ROOT/path) != expected:
            raise ValueError('Frozen computation input changed: '+path)
    revisions = []
    for path, expected in preflight['protected'].items():
        actual = sha(ROOT/path)
        if actual != expected:
            if not path.startswith('paper/'):
                raise ValueError('Earlier scan changed: '+path)
            revisions.append(dict(path=path, before_sha256=expected, after_sha256=actual))
    original = json.loads((OUT/'report.json').read_text())
    if output is None:
        folder = Path(tempfile.mkdtemp(prefix='rrq-step-replay-'))
    else:
        folder = Path(output); folder.mkdir(parents=True)
    decoder = ColdDecoder(folder/'decoder')
    try:
        for row in original['cases']:
            if row['status'] != 'SELECTED_DECODED_AND_EXACTLY_AUDITED':
                raise ValueError('Incomplete experiment')
            packet = ROOT/row['packet']
            if sha(packet) != row['packet_sha256'] or packet.stat().st_size != row['selected_bytes']:
                raise ValueError('Saved packet changed')
            y, m, p, info = decoder.decode(packet)
            with np.load(ROOT/row['source'], allow_pickle=False) as data:
                x, mask = data['raw'].astype(np.int64), data['mask'].astype(bool)
            x[mask] = 0
            a = audit(x, y, mask, m, mask, p, cap=row['cap'])
            if a != row['audit'] or not legal(a, row['epsilon']) or info['source_provided']:
                raise ValueError('Exact winner audit changed')
        if summary(original['cases'], preflight) != original:
            raise ValueError('Saved aggregate statistics changed')
        save(folder/'validation.json', dict(status='PASS_16_SAVED_WINNERS_AFTER_NARRATIVE_REVISION',
            source_free_decodes=decoder.count, exact_rectangle_audits=decoder.count,
            computation_inputs_and_previous_measurements_unchanged=True,
            aggregates_identical=True, requested_manuscript_revisions=revisions))
        print(json.dumps(dict(status='PASS_16_SAVED_WINNERS', source_free_decodes=decoder.count,
                              receipt=str(folder/'validation.json'))))
    finally:
        decoder.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', help='New receipt directory; default is outside the checkout')
    main(parser.parse_args().output)
