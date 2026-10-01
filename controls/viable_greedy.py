"""Classical interval viability plus coarse-first greedy, an O(HW) control."""
from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def row_greedy(x, up, band, step, cap, protected):
    width = len(x)
    # low[j], high[j] are suffix-viable states BEFORE source column j.
    low = np.empty(width+1, np.int64)
    high = np.empty(width+1, np.int64)
    low[width], high[width] = -band, band
    for j in range(width-1, -1, -1):
        delta = up[j] - (up[j-1] if j else 0)
        if protected[j]:
            low[j] = max(-band, low[j+1]-delta)
            high[j] = min(band, high[j+1]-delta)
        else:
            t = x[j]-delta
            low[j] = max(-band, low[j+1]+t-cap)
            high[j] = min(band, high[j+1]+t)
        if low[j] > high[j]:
            raise RuntimeError('Full-integer suffix unexpectedly infeasible')
    if not low[0] <= 0 <= high[0]:
        raise RuntimeError('Initial state unexpectedly infeasible')
    out = np.empty(width, np.int64)
    state = np.empty(width, np.int64)
    a = np.int64(0)
    fine = np.int64(0)
    energy = np.int64(0)
    for j in range(width):
        delta = up[j] - (up[j-1] if j else 0)
        t = x[j]-delta
        if protected[j]:
            b = a+delta
            if not low[j+1] <= b <= high[j+1]:
                raise RuntimeError('Protected transition left viable corridor')
        else:
            lo = max(low[j+1], a-t)
            hi = min(high[j+1], a-t+cap)
            if lo > hi:
                raise RuntimeError('Greedy state left viable corridor')
            residue = (a-t) % step
            kmin = -((residue-lo)//step)
            kmax = (hi-residue)//step
            if kmin <= kmax:
                # Closest-to-zero lattice states; tie selects the smaller state.
                k = min(max((-residue)//step, kmin), kmax)
                b = residue+k*step
                if k < kmax:
                    alternative = b+step
                    if alternative*alternative < b*b:
                        b = alternative
            else:
                b = min(max(0, lo), hi)
        value = t+b-a
        if not 0 <= value <= cap or not -band <= b <= band:
            raise RuntimeError('Physical/prefix transition violation')
        out[j], state[j] = value, b
        fine += 1 if value % step else 0
        energy += b*b
        a = b
    return out, state, fine, energy


def reconstruct(x, band, step, cap=10000, protected=None):
    x = np.asarray(x)
    if x.ndim != 2 or not x.size or not np.issubdtype(x.dtype, np.integer):
        raise ValueError('Nonempty 2D integer source required')
    for value in (band, step, cap):
        if not isinstance(value, (int, np.integer)) or isinstance(value, (bool, np.bool_)):
            raise TypeError('Integer parameters required')
    band, step, cap = int(band), int(step), int(cap)
    if not 0 <= band <= 10000 or not 0 < step <= 2**30 or not 0 <= cap <= 2**30:
        raise ValueError('Parameter safety scope')
    if x.min() < 0 or x.max() > cap or x.size*cap > 2**53-1:
        raise ValueError('Source range/sum safety scope')
    x = x.astype(np.int64)
    protected = np.zeros(x.shape, bool) if protected is None else np.asarray(protected, bool)
    if protected.shape != x.shape:
        raise ValueError('Protected mask shape')
    y = np.empty_like(x)
    up = np.zeros(x.shape[1], np.int64)
    counts = []
    for i in range(x.shape[0]):
        y[i], up, fine, _ = row_greedy(x[i], up, band, step, cap, protected[i])
        counts.append(int(fine))
    prefix = (y-x).cumsum(0).cumsum(1)
    if np.abs(prefix).max() > band or not np.array_equal(y[protected], x[protected]):
        raise RuntimeError('Full-field invariant')
    return y, dict(off_lattice=int(np.count_nonzero(y % step)),
                   row_greedy_off_lattice=counts, max_abs_prefix=int(np.abs(prefix).max()),
                   changed=int(np.count_nonzero(y != x)))
