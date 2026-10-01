"""Decode a delivered file without sources or the historical launch environment.

Native scientific streams use the caller's DCC_NATIVE_PYTHON,
DCC_NATIVE_MGARD_DRIVER and DCC_QPET_API_V2_DRIVER settings. Integer and
RangeRectQuant streams need only the included Python dependencies.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT.parent / 'LinewiseROI/experiments')]
from controls.research_packet import decode as decode_field


def decode_file(packet, output):
    packet, output = Path(packet), Path(output)
    if output.exists():
        raise ValueError('Choose a new output path')
    os.environ.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    blob = packet.read_bytes()
    commands = []
    if blob[:4] == b'RRF2':
        y, mask, protected, metadata = decode_field(blob)
    elif blob[:4] == b'RWS1':
        from controls.water_packet import decode
        y, mask, protected, metadata = decode(blob, commands)
    elif blob[:4] == b'BA02':
        from built_area_discrete_packet import decode
        y, mask, metadata, _ = decode(blob, commands)
        protected = mask.copy()
    else:
        raise ValueError('Unsupported delivered file magic')
    y = np.asarray(y, np.int64)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, y=y, mask=mask, protected=protected,
                        metadata_json=np.array(json.dumps(metadata, sort_keys=True)))
    return dict(status='DECODED', source_provided=False, packet_sha256=hashlib.sha256(blob).hexdigest(),
                numerator_sha256=hashlib.sha256(y.astype('<i8').tobytes()).hexdigest(),
                denominator=metadata.get('denominator', 1),
                shape=list(y.shape), native_commands=commands, output=str(output.resolve()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(decode_file(args.packet, args.output), indent=2))
