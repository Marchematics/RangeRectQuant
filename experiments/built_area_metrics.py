"""All-rectangle interval audit and common full-field query endpoint."""
from __future__ import annotations

from fractions import Fraction
import math

import numpy as np
from numba import njit


@njit(cache=True)
def _rectangle_bounds(lo, hi):
    h, w = lo.shape
    max_lo = 0.
    max_hi = 0.
    min_lo = 0.
    min_hi = 0.
    for top in range(h):
        columns_lo = np.zeros(w)
        columns_hi = np.zeros(w)
        for bottom in range(top, h):
            upper_max_end = 0.
            lower_max_end = 0.
            upper_min_end = 0.
            lower_min_end = 0.
            for j in range(w):
                columns_lo[j] = np.nextafter(columns_lo[j] + lo[bottom, j], -np.inf)
                columns_hi[j] = np.nextafter(columns_hi[j] + hi[bottom, j], np.inf)
                a, b = columns_lo[j], columns_hi[j]
                lower_max_end = max(a, np.nextafter(lower_max_end + a, -np.inf))
                upper_max_end = max(b, np.nextafter(upper_max_end + b, np.inf))
                lower_min_end = min(a, np.nextafter(lower_min_end + a, -np.inf))
                upper_min_end = min(b, np.nextafter(upper_min_end + b, np.inf))
                max_lo = max(max_lo, lower_max_end)
                max_hi = max(max_hi, upper_max_end)
                min_lo = min(min_lo, lower_min_end)
                min_hi = min(min_hi, upper_min_end)
    return max(max_lo, -min_hi), max(max_hi, -min_lo)


def rectangle_interval(x, y):
    x, y = np.asarray(x, np.float64), np.asarray(y, np.float64)
    if (x.ndim != 2 or x.shape != y.shape or min(x.shape) < 1 or max(x.shape) > 1024 or
            not np.isfinite(x).all() or not np.isfinite(y).all() or
            np.abs(x).max() > 10000 or np.abs(y).max() > 10000):
        raise ValueError('Finite capped area arrays required')
    if np.array_equal(x, y):
        return 0., 0.
    difference = y - x
    lo, hi = np.nextafter(difference, -np.inf), np.nextafter(difference, np.inf)
    return _rectangle_bounds(lo, hi)


def queries(shape, count=1024):
    h, w = shape
    rng = np.random.default_rng(20261001)
    output = []
    while len(output) < count:
        top, bottom = sorted(rng.integers(0, h + 1, size=2).tolist())
        left, right = sorted(rng.integers(0, w + 1, size=2).tolist())
        if top != bottom and left != right:
            output.append([top, bottom, left, right])
    return np.asarray(output, dtype=np.int64)


def cache(y, mask):
    sums = np.pad(y.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    counts = np.pad((~mask).astype(np.int64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    return sums, counts


def query(cached, rectangle):
    top, bottom, left, right = map(int, rectangle)
    sums, counts = cached
    n = int(counts[bottom, right] - counts[top, right] - counts[bottom, left] + counts[top, left])
    value = float(sums[bottom, right] - sums[top, right] - sums[bottom, left] + sums[top, left])
    return (value if n else None), n


def cache_rounding_bound(y):
    """All rectangles: sequential two-axis cache plus three corner operations."""
    y = np.asarray(y, np.float64)
    if y.ndim != 2 or not np.isfinite(y).all() or np.any(y < 0) or np.any(y > 10000):
        raise ValueError('Nonnegative finite legal proxy required')
    if not y.any():
        return 0.
    up = lambda value: float(np.nextafter(value, np.inf))
    total = up(math.fsum(y.ravel()))
    length = sum(y.shape)
    gamma = up(float(Fraction(length, 2**53 - length)))
    gamma3 = up(float(Fraction(3, 2**53 - 3)))
    # A deliberately loose positive absolute term covers subnormal operations;
    # every other addition/multiplication of bounds is outward-rounded as well.
    tiny = up(float(np.finfo(np.float64).tiny) * y.size * (length + 4))
    node = up(up(gamma * total) + tiny)
    corners = up(up(gamma3 * up(4 * up(total + node))) + tiny)
    return up(up(4 * node) + corners)


def service_contract(x, y, mask, decoded_mask, epsilon):
    masks_equal = bool(np.array_equal(mask, decoded_mask))
    finite = bool(np.isfinite(y).all())
    range_ok = bool(finite and np.all((y[~mask] >= 0) & (y[~mask] <= 10000)))
    missing_ok = bool(masks_equal and finite and not y[mask].any())
    if not range_ok or not missing_ok:
        return dict(status='ILLEGAL', mask_ok=missing_ok, range_ok=range_ok)
    lower, upper = rectangle_interval(x, y)
    rounding = cache_rounding_bound(y)
    query_upper = float(np.nextafter(upper + rounding, np.inf)) if upper or rounding else 0.
    query_lower = max(0., float(np.nextafter(lower - rounding, -np.inf)))
    status = 'LEGAL' if query_upper <= epsilon else 'ILLEGAL' if query_lower > epsilon else 'UNCERTIFIED'
    return dict(status=status, mask_ok=missing_ok, range_ok=range_ok,
                all_rectangle_field_error_lower=lower, all_rectangle_field_error_upper=upper,
                all_rectangle_cache_query_rounding_upper=rounding,
                all_rectangle_query_error_lower=query_lower,
                all_rectangle_query_error_upper=query_upper,
                changed_values=int(np.count_nonzero(x != y)))
