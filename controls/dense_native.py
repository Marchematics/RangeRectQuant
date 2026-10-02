"""Extend only the accepted settings of the frozen native integer adapter.

The original module remains byte-identical. Its codec, carrier, postprocessor
and digest functions execute in an isolated module namespace with the larger
explicit allowlist. This changes no codec implementation or decoded value.
"""
import importlib.util
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[2]/'LinewiseROI/experiments/built_area_discrete_packet.py'
spec=importlib.util.spec_from_file_location('_review_dense_discrete',SOURCE)
core=importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
ORIGINAL=core.grid()
ADDED_BOUNDS=(.25,.375,.625,.75,.875,1.5,2.,3.,6.,8.,12.,24.,32.)


def added_grid():
    templates=[c for c in ORIGINAL if c.get('dtype')=='float64' and c['bound']==.49]
    rows=[dict(c,bound=b) for c in templates for b in ADDED_BOUNDS]
    rows.extend(dict(backend='sz3',dtype='int64',algorithm=a,bound=b,transform='direct')
                for a in ('INTERP_LORENZO','INTERP','LORENZO_REG') for b in (1.,2.,4.,8.,16.))
    assert len(rows)==106
    return rows


def allowed_grid():
    return ORIGINAL+added_grid()


core.grid=allowed_grid
encode=core.encode
decode=core.decode
