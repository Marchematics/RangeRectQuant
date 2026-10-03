"""Select a quantization step by complete-file length at a fixed error budget.

The construction and RRF2 transport are unchanged. Exhaustive mode searches
all transport-valid steps 1..65536; supplied candidates give a restricted optimum.
The selected step is already present in the ordinary file metadata. The search
ledger is encoder-side evidence and is not required by a source-free decoder.
"""
from __future__ import annotations

import hashlib
import json
import time
import zlib

import numpy as np

from controls import research_packet
from controls.viable_greedy import reconstruct


def _integer(value, name):
    if not isinstance(value, (int, np.integer)) or isinstance(value, (bool, np.bool_)):
        raise TypeError(f'{name} must be an integer')
    return int(value)


def _large_step_variants(packet, steps):
    """Exactly minimize metadata cost for the identical field at steps > cap.

    Only zero is a coarse value beyond cap. The constructor then follows the
    same path, and every quotient is zero and every remainder equals the field.
    The four array/mask streams and reconstruction digest can be reused. Step
    numbers can still change compressed JSON size, so none are discarded.
    """
    magic, h, w, *rest = research_packet.HEADER.unpack_from(packet)
    lengths, digest = list(rest[:-1]), rest[-1]
    offset = research_packet.HEADER.size + sum(lengths[:4])
    meta = json.loads(zlib.decompress(packet[offset:-32]))
    if meta['codec'] != 'quotient-remainder-lzma6' or any(q <= meta['cap'] for q in steps):
        raise ValueError('Large-step equivalence requires a zero quotient alphabet')
    started = time.perf_counter()
    fixed_bytes = len(packet)-lengths[4]
    best_key = best_metadata = None
    histogram = {}
    for q in steps:
        meta['step'] = q
        meta['method']['quantization_step'] = q
        raw = json.dumps(meta, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        metadata = zlib.compress(raw, 9)
        if len(metadata) > 16384 or len(raw) > 65536:
            raise ValueError('Metadata outside transport scope')
        histogram[len(metadata)] = histogram.get(len(metadata), 0)+1
        key = (fixed_bytes+len(metadata), q)
        if best_key is None or key < best_key:
            best_key, best_metadata = key, metadata
    lengths[4] = len(best_metadata)
    body = (research_packet.HEADER.pack(magic, h, w, *lengths, digest)
            + packet[research_packet.HEADER.size:offset] + best_metadata)
    selected = body + hashlib.sha256(body).digest()
    return selected, dict(candidate_count=len(steps), base_step=steps[0],
                          best_step=best_key[1], best_bytes=best_key[0],
                          metadata_length_histogram=histogram,
                          metadata_search_seconds=time.perf_counter()-started,
                          identical_construction_and_array_streams=True)


def encode_selected(x, epsilon, cap, mask=None, protected=None, candidates=None,
                    config=None, geo=None):
    """Return (packet, reconstruction, ledger), minimizing (file bytes, step).

    All candidates use the same masks, geospatial metadata and encoder. Their
    lengths include streams, masks, metadata, digest and checksum. A full search
    is exact over all 65536 transport-valid steps, not over all jointly legal
    fields. Steps above cap share one construction and array encoding; their
    metadata lengths are evaluated exactly. Other trials each construct/encode.
    """
    epsilon, cap = _integer(epsilon, 'epsilon'), _integer(cap, 'cap')
    if not 0 <= epsilon // 4 <= 10000 or epsilon < 0:
        raise ValueError('Error budget outside the construction safety scope')
    if not 0 <= cap <= 32767:
        raise ValueError('cap must fit every signed-quotient candidate')
    x = np.asarray(x)
    if (x.ndim != 2 or not x.size or x.size > research_packet.MAX_PIXELS
            or not np.issubdtype(x.dtype, np.integer)):
        raise ValueError('Nonempty two-dimensional integer source required')
    if x.min() < 0 or x.max() > cap:
        raise ValueError('Source outside the declared range')
    x = x.astype(np.int64)
    mask = np.zeros(x.shape, bool) if mask is None else np.asarray(mask, bool)
    protected = np.zeros(x.shape, bool) if protected is None else np.asarray(protected, bool)
    if mask.shape != x.shape or protected.shape != x.shape:
        raise ValueError('Mask shape mismatch')
    if x[mask].any():
        raise ValueError('Missing samples must be represented by zero')
    protected = protected | mask
    if config is not None and not isinstance(config, dict):
        raise TypeError('config must be a dictionary')
    if geo is not None and not isinstance(geo, dict):
        raise TypeError('geo must be a dictionary')
    steps = list(range(1, 65537)) if candidates is None else [
        _integer(q, 'candidate step') for q in candidates]
    if not steps or any(not 1 <= q <= 65536 for q in steps):
        raise ValueError('Nonempty transport-valid candidate set required')
    steps = sorted(set(steps))
    complete_domain = steps == list(range(1, 65537))
    canonical_domain = steps == list(range(1, cap+2))
    small_steps = [q for q in steps if q <= cap]
    large_steps = [q for q in steps if q > cap]
    construction_steps = small_steps + large_steps[:1]
    band = epsilon // 4
    started = time.perf_counter()
    best_key = best_packet = best_y = None
    rows = []
    tail = None
    for q in construction_steps:
        tick = time.perf_counter()
        y, construction = reconstruct(x, band, q, cap, protected)
        method = dict(config or {})
        method.update(family='RangeRectQuant', epsilon=epsilon, quantization_step=q)
        packet, fees = research_packet.encode(y, mask, q, cap, method, geo or {}, protected)
        if sum(fees.values()) != len(packet):
            raise RuntimeError('Complete-file fee mismatch')
        rows.append(dict(step=q, packet_bytes=len(packet), fees=fees,
                         fine_pixels=construction['off_lattice'],
                         changed_pixels=construction['changed'],
                         max_abs_prefix_error=construction['max_abs_prefix'],
                         construction_and_encoding_seconds=time.perf_counter()-tick))
        if q > cap:
            packet, tail = _large_step_variants(packet, large_steps)
            q = tail['best_step']
        key = (len(packet), q)
        if best_key is None or key < best_key:
            best_key, best_packet, best_y = key, packet, y
    # This check receives no source; it validates the delivered file itself.
    decoded, decoded_mask, decoded_protected, metadata = research_packet.decode(best_packet)
    if (not np.array_equal(decoded, best_y) or not np.array_equal(decoded_mask, mask)
            or not np.array_equal(decoded_protected, protected)):
        raise RuntimeError('Selected packet did not recover the selected field')
    if metadata['step'] != best_key[1]:
        raise RuntimeError('Selected-step metadata mismatch')
    detail = dict(epsilon=epsilon, band=band, cap=cap,
                  candidate_steps=None if complete_domain else steps,
                  candidate_domain=[1, 65536] if complete_domain else None,
                  candidate_count=len(steps),
                  complete_transport_domain=complete_domain,
                  complete_canonical_domain=canonical_domain,
                  optimality_scope='all transport-valid steps' if complete_domain else 'supplied candidate set',
                  full_construction_trials=len(construction_steps),
                  large_step_equivalence=tail,
                  selected_step=best_key[1], selected_bytes=best_key[0],
                  tie_break='smaller step', rows=rows,
                  elapsed_seconds=time.perf_counter()-started,
                  selected_packet_decoded_without_source=True)
    return best_packet, best_y, detail
