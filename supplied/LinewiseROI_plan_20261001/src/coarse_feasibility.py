"""Exact zero-fine feasibility for a fixed incoming row of prefix errors.

This is a diagnostic, not the optimizer used in the recorded payload screens.
It certifies whether a row can be written using only multiples of `step`.
"""
from __future__ import annotations
import numpy as np


def coarse_row_feasible(x, up, band: int, step: int, cap: int, protected=None):
    x = np.asarray(x, dtype=np.int64)
    up = np.asarray(up, dtype=np.int64)
    if x.ndim != 1 or x.size == 0 or up.shape != x.shape:
        raise ValueError('Expected matching nonempty rows')
    if band < 0 or step <= 0 or cap < 0:
        raise ValueError('Invalid band, step or cap')
    if np.any(x < 0) or np.any(x > cap) or np.any(np.abs(up) > band):
        raise ValueError('Invalid source or incoming prefix error')
    if protected is None:
        protected = np.zeros(x.size, dtype=bool)
    protected = np.asarray(protected, dtype=bool)
    if protected.shape != x.shape:
        raise ValueError('Protected row shape mismatch')
    lo = [0]; hi = [0]; sx = 0; max_increment = cap // step
    for j in range(x.size):
        sx += int(x[j])
        v = sx - int(up[j])
        left = -(-(v-band) // step)
        right = (v+band) // step
        if protected[j]:
            if int(x[j]) % step:
                return {'feasible': False, 'first_blocked_column': j, 'reason': 'protected_off_lattice'}
            k = int(x[j]) // step
            lower = max(left, lo[-1]+k)
            upper = min(right, hi[-1]+k)
        else:
            lower = max(left, lo[-1])
            upper = min(right, hi[-1]+max_increment)
        if lower > upper:
            return {'feasible': False, 'first_blocked_column': j, 'reason': 'empty_reachable_interval'}
        lo.append(lower); hi.append(upper)
    # Any endpoint inside the final interval has a feasible predecessor chain.
    k = lo[-1]; out = np.empty(x.size, dtype=np.int64)
    for j in range(x.size-1, -1, -1):
        if protected[j]:
            prev = k-int(x[j])//step
        else:
            prev = max(lo[j], k-max_increment)
            if prev > min(hi[j], k):
                raise AssertionError('Broken interval recurrence')
        out[j] = step*(k-prev); k = prev
    error = up + np.cumsum(out-x)
    assert k == 0 and np.max(np.abs(error)) <= band
    assert np.all(out >= 0) and np.all(out <= cap)
    assert np.all(out % step == 0)
    assert np.array_equal(out[protected], x[protected])
    return {'feasible': True, 'reconstruction': out, 'prefix_error': error}
