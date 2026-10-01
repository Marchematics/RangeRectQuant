"""QF01 matched carrier for saved-DP fields and the viable-greedy control."""
from __future__ import annotations

import hashlib
import json
import zlib

import numpy as np
from range_rect_quant.packet import (
    HEADER, BODY_HEADER, SETTINGS, digest, bounded_zlib, pack_mask, unpack_mask,
    pack_u16, unpack_u16,
)

CODEC = dict(backend='legal-field-attribution-control', version=1,
             coder='u16-byte-shuffle-lzma6', algorithm_ids={'0': 'saved-frozen-row-dp', '1': 'viable-greedy'})
MODES = ('lossy', 'zero-preserve')


def encode(x, y, mask, step, mode, algorithm_id, geo):
    x, y, mask = np.asarray(x), np.asarray(y), np.asarray(mask, bool)
    if (type(step) is not int or step not in SETTINGS or mode not in MODES or
            type(algorithm_id) is not int or algorithm_id not in (0, 1) or
            x.ndim != 2 or not x.size or max(x.shape) > 1024 or y.shape != x.shape or mask.shape != x.shape or
            not np.issubdtype(x.dtype, np.integer) or not np.issubdtype(y.dtype, np.integer) or
            x.min() < 0 or x.max() > 10000 or y.min() < 0 or y.max() > 10000 or
            x[mask].any() or y[mask].any()):
        raise ValueError('Legal integer source/field and fixed attribution configuration required')
    x, y = x.astype(np.int64), y.astype(np.int64)
    epsilon, band = SETTINGS[step]
    if np.abs((y-x).cumsum(0).cumsum(1)).max() > band:
        raise ValueError('Field fails the full prefix invariant')
    protected = (x == 0) & ~mask if mode == 'zero-preserve' else np.zeros(x.shape, bool)
    if y[protected].any():
        raise ValueError('Declared source-zero protection failed')
    parts = (pack_u16(y//step), pack_u16(y % step), pack_mask(protected))
    body = BODY_HEADER.pack(*(len(part) for part in parts))+b''.join(parts)
    meta = dict(codec=CODEC, algorithm_id=algorithm_id, step=step, mode=mode, epsilon=epsilon, band=band,
                geo=geo, units='m2', epsilons=[100, 1000], output='float64_integer',
                postprocessor='none', missing_zero=True, common_full_field_query_service=1,
                guaranteed_rectangle_bound=4*band, source_zero_preservation=mode == 'zero-preserve',
                bidirectional_zero_support_preservation=False)
    config = zlib.compress(json.dumps(meta, sort_keys=True, separators=(',', ':')).encode(), 9)
    if len(config) > 16384:
        raise ValueError('Configuration size')
    missing = pack_mask(mask)
    head = HEADER.pack(b'QF01', *x.shape, len(missing), len(config), len(body), digest(y, mask))
    packet = head+missing+config+body
    packet += hashlib.sha256(packet).digest()
    fees = dict(header_bytes=len(head), checksum_bytes=32, mask_bytes=len(missing),
                config_bytes=len(config), body_bytes=len(body))
    detail = dict(body_header_bytes=BODY_HEADER.size, quotient_bytes=len(parts[0]),
                  remainder_bytes=len(parts[1]), source_zero_bitmap_bytes=len(parts[2]))
    return packet, body, dict(fees=fees, body_detail=detail)


def decode(packet):
    if len(packet) < HEADER.size+32 or hashlib.sha256(packet[:-32]).digest() != packet[-32:]:
        raise ValueError('QF01 checksum/length')
    magic, h, w, ml, cl, bl, expected = HEADER.unpack_from(packet)
    if magic != b'QF01' or min(h, w) < 1 or max(h, w) > 1024 or cl > 16384 or len(packet) != HEADER.size+ml+cl+bl+32:
        raise ValueError('QF01 shape/components')
    offset = HEADER.size
    mask = unpack_mask(packet[offset:offset+ml], (h, w))
    offset += ml
    meta = json.loads(bounded_zlib(packet[offset:offset+cl], 65536))
    step, mode, algorithm = meta['step'], meta['mode'], meta['algorithm_id']
    if type(step) is not int or step not in SETTINGS or mode not in MODES or type(algorithm) is not int or algorithm not in (0, 1):
        raise ValueError('Fixed attribution configuration')
    epsilon, band = SETTINGS[step]
    required = dict(codec=CODEC, epsilon=epsilon, band=band, units='m2', epsilons=[100, 1000],
                    output='float64_integer', postprocessor='none', missing_zero=True,
                    common_full_field_query_service=1, guaranteed_rectangle_bound=4*band,
                    source_zero_preservation=mode == 'zero-preserve', bidirectional_zero_support_preservation=False)
    if any(meta.get(k) != v for k, v in required.items()):
        raise ValueError('Paid metadata mismatch')
    offset += cl
    body = packet[offset:offset+bl]
    if len(body) < BODY_HEADER.size:
        raise ValueError('Truncated body')
    lengths = BODY_HEADER.unpack_from(body)
    if BODY_HEADER.size+sum(lengths) != len(body):
        raise ValueError('Body lengths')
    parts, position = [], BODY_HEADER.size
    for length in lengths:
        parts.append(body[position:position+length]); position += length
    quotient = unpack_u16(parts[0], (h, w), 10000//step)
    remainder = unpack_u16(parts[1], (h, w), step-1)
    protected = unpack_mask(parts[2], (h, w))
    if mode != 'zero-preserve' and parts[2]:
        raise ValueError('Unexpected protection bitmap')
    y = step*quotient+remainder
    if np.any(y > 10000) or y[mask].any() or y[protected].any() or (mask & protected).any():
        raise ValueError('Decoded field/mask/protected zero')
    y = y.astype(np.float64)
    if digest(y, mask) != expected:
        raise ValueError('Decoded digest')
    return y, mask, meta, protected
