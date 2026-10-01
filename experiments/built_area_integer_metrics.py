"""Exact all-rectangle contract for bounded integer area fields."""
from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def _maximum_rectangle(difference):
    h, w = difference.shape
    maximum = np.int64(0)
    for top in range(h):
        columns = np.zeros(w, dtype=np.int64)
        for bottom in range(top, h):
            maximum_end = np.int64(0)
            minimum_end = np.int64(0)
            for j in range(w):
                columns[j] += difference[bottom, j]
                v = columns[j]
                maximum_end = max(v, maximum_end + v)
                minimum_end = min(v, minimum_end + v)
                maximum = max(maximum, maximum_end, -minimum_end)
    return maximum


def integer_error(x, y, mask, decoded_mask):
    x, y = np.asarray(x, np.float64), np.asarray(y, np.float64)
    mask, decoded_mask = np.asarray(mask, bool), np.asarray(decoded_mask, bool)
    if (x.ndim != 2 or min(x.shape) < 1 or max(x.shape) > 1024 or y.shape != x.shape or
            mask.shape != x.shape or decoded_mask.shape != x.shape):
        raise ValueError('Integer field shapes')
    for a in (x, y):
        if (not np.isfinite(a).all() or np.any((a < 0) | (a > 10000)) or
                not np.array_equal(a, np.rint(a))):
            raise ValueError('Finite bounded integer field required')
    if x[mask].any():
        raise ValueError('Source missing values must be zero')
    if not np.array_equal(mask, decoded_mask) or y[mask].any():
        return dict(mask_ok=False, range_ok=True, integer_cache_query_exact=True)
    error = 0 if np.array_equal(x, y) else int(_maximum_rectangle(y.astype(np.int64) - x.astype(np.int64)))
    # Any partial sum/corner operation stays below 4*1024^2*10000 < 2^53.
    return dict(mask_ok=True, range_ok=True, all_rectangle_query_error_exact=error,
                integer_cache_query_exact=True, changed_values=int(np.count_nonzero(x != y)))


def contract(error, epsilon):
    if not np.isfinite(epsilon) or epsilon < 0:
        raise ValueError('Nonnegative finite budget')
    legal = error['mask_ok'] and error['range_ok'] and error['all_rectangle_query_error_exact'] <= epsilon
    return dict(status='LEGAL' if legal else 'ILLEGAL', **error)
