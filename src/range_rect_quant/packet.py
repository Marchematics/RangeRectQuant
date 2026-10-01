"""RQ01: fully paid, source-free quotient/remainder field transport."""
from __future__ import annotations

import hashlib
import json
import lzma
import struct
import zlib

import numpy as np

HEADER = struct.Struct('<4sIIIII32s')
BODY_HEADER = struct.Struct('<3I')
MODES = ('lossy', 'zero-preserve', 'identity')
SETTINGS = {20: (100, 25), 200: (1000, 250)}
CODEC = dict(backend='range-rect-quant', version=1, coder='u16-byte-shuffle-lzma6',
             scan='raster-rows', objective='lex(off-lattice,row-prefix-squared)',
             tie='lower-state-index', refinement=False)


def digest(y, mask):
    return hashlib.sha256(y.astype('<f8').tobytes() + mask.tobytes()).digest()


def bounded_zlib(raw, maximum):
    d = zlib.decompressobj()
    data = d.decompress(raw, maximum + 1)
    if len(data) > maximum or not d.eof or d.unused_data or d.unconsumed_tail:
        raise ValueError('Compressed metadata/mask length or trailing bytes')
    return data


def pack_mask(mask):
    return zlib.compress(np.packbits(mask.ravel(), bitorder='little').tobytes(), 9) if mask.any() else b''


def unpack_mask(raw, shape):
    n = int(np.prod(shape))
    if not raw:
        return np.zeros(shape, bool)
    data = bounded_zlib(raw, (n + 7) // 8)
    if len(data) != (n + 7) // 8:
        raise ValueError('Mask length')
    bits = np.unpackbits(np.frombuffer(data, 'u1'), bitorder='little')
    if bits[n:].any():
        raise ValueError('Mask padding')
    return bits[:n].reshape(shape).astype(bool)


def pack_u16(a):
    raw = np.asarray(a, '<u2').tobytes()
    return lzma.compress(np.frombuffer(raw, 'u1').reshape(-1, 2).T.copy().tobytes(), preset=6)


def unpack_u16(raw, shape, maximum):
    n = int(np.prod(shape))
    d = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    data = d.decompress(raw, max_length=2 * n + 1)
    if len(data) != 2 * n or not d.eof or d.unused_data:
        raise ValueError('Quotient/remainder length or trailing compressed bytes')
    a = np.frombuffer(np.frombuffer(data, 'u1').reshape(2, n).T.copy().tobytes(), '<u2').astype(np.int64).reshape(shape)
    if np.any(a > maximum):
        raise ValueError('Quotient/remainder range')
    return a


def encode(x, mask, step, mode, geo):
    from .corridor import reconstruct
    x, mask = np.asarray(x), np.asarray(mask, bool)
    if (type(step) is not int or step not in SETTINGS or mode not in MODES or x.ndim != 2 or
            min(x.shape) < 1 or max(x.shape) > 1024 or mask.shape != x.shape or
            not np.isfinite(x).all() or np.any((x < 0) | (x > 10000)) or
            not np.array_equal(x, np.rint(x)) or x[mask].any()):
        raise ValueError('Legal integer source/mask and frozen mode required')
    source = x.astype(np.int64)
    epsilon, band = SETTINGS[step]
    zero_protect = (source == 0) & ~mask if mode == 'zero-preserve' else np.zeros(x.shape, bool)
    if mode == 'identity':
        y = source.copy()
        info = dict(off_lattice=int(np.count_nonzero(y % step)), row_min_off_lattice=[],
                    max_abs_prefix=0, changed=0)
    else:
        y, info = reconstruct(source, band, step, 10000, mask | zero_protect)
    parts = (pack_u16(y // step), pack_u16(y % step), pack_mask(zero_protect))
    body = BODY_HEADER.pack(*(len(a) for a in parts)) + b''.join(parts)
    meta = dict(codec=CODEC, step=step, mode=mode, epsilon=epsilon, band=band,
        geo=geo, units='m2', epsilons=[100, 1000], output='float64_integer', postprocessor='none',
        missing_zero=True, common_full_field_query_service=1,
        guaranteed_rectangle_bound=0 if mode == 'identity' else 4 * band,
        source_zero_preservation=mode == 'zero-preserve', bidirectional_zero_support_preservation=False)
    config = zlib.compress(json.dumps(meta, sort_keys=True, separators=(',', ':')).encode(), 9)
    if len(config) > 16384:
        raise ValueError('Metadata too large')
    mb = pack_mask(mask)
    head = HEADER.pack(b'RQ01', *x.shape, len(mb), len(config), len(body), digest(y, mask))
    packet = head + mb + config + body
    packet += hashlib.sha256(packet).digest()
    fees = dict(header_bytes=HEADER.size, checksum_bytes=32, mask_bytes=len(mb),
        config_bytes=len(config), body_bytes=len(body))
    detail = dict(body_header_bytes=BODY_HEADER.size, quotient_bytes=len(parts[0]),
        remainder_bytes=len(parts[1]), source_zero_bitmap_bytes=len(parts[2]),
        protected_source_zeros=int(zero_protect.sum()),
        source_valid_zeros=int(np.count_nonzero((source == 0) & ~mask)),
        changed_source_valid_zeros=int(np.count_nonzero((source == 0) & ~mask & (y != 0))))
    return packet, body, dict(fees=fees, body_detail=detail, quantizer=info)


def decode(packet):
    if len(packet) < HEADER.size + 32 or hashlib.sha256(packet[:-32]).digest() != packet[-32:]:
        raise ValueError('RQ01 checksum/length')
    magic, h, w, ml, cl, bl, expected = HEADER.unpack_from(packet)
    if magic != b'RQ01' or min(h, w) < 1 or max(h, w) > 1024 or cl > 16384 or len(packet) != HEADER.size + ml + cl + bl + 32:
        raise ValueError('RQ01 dimensions/components')
    offset = HEADER.size
    mask = unpack_mask(packet[offset:offset + ml], (h, w))
    offset += ml
    meta = json.loads(bounded_zlib(packet[offset:offset + cl], 65536))
    step, mode = meta['step'], meta['mode']
    if type(step) is not int or step not in SETTINGS or mode not in MODES:
        raise ValueError('Frozen step/mode')
    epsilon, band = SETTINGS[step]
    required = dict(codec=CODEC, epsilon=epsilon, band=band, units='m2', epsilons=[100, 1000],
        output='float64_integer', postprocessor='none', missing_zero=True, common_full_field_query_service=1,
        guaranteed_rectangle_bound=0 if mode == 'identity' else 4 * band,
        source_zero_preservation=mode == 'zero-preserve', bidirectional_zero_support_preservation=False)
    if any(meta.get(k) != v for k, v in required.items()):
        raise ValueError('Frozen paid metadata')
    offset += cl
    body = packet[offset:offset + bl]
    if len(body) < BODY_HEADER.size:
        raise ValueError('Truncated body')
    lengths = BODY_HEADER.unpack_from(body)
    if BODY_HEADER.size + sum(lengths) != len(body):
        raise ValueError('Body lengths')
    parts, position = [], BODY_HEADER.size
    for length in lengths:
        parts.append(body[position:position + length]); position += length
    quotient = unpack_u16(parts[0], (h, w), 10000 // step)
    remainder = unpack_u16(parts[1], (h, w), step - 1)
    zero_protect = unpack_mask(parts[2], (h, w))
    if mode != 'zero-preserve' and parts[2]:
        raise ValueError('Unpaid/undeclared protection data')
    y = step * quotient + remainder
    if np.any(y > 10000) or y[mask].any() or y[zero_protect].any() or (mask & zero_protect).any():
        raise ValueError('Physical field/missing/protected zero')
    y = y.astype(np.float64)
    if digest(y, mask) != expected:
        raise ValueError('Full decoded digest')
    return y, mask, meta, zero_protect
