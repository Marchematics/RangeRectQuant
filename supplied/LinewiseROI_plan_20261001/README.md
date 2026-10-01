# Range-constrained raster quantization — research probe

Read `研究计划.md` for the plan and `PROOF_NOTES.md` for the derivations.

This is a local research artifact for a proposed next method in the LinewiseROI project. It is **not a replacement repository, not a complete geospatial codec, and not a new real-data benchmark result**. The original GitHub repository was only read. No remote files or user's local files were changed.

## Implemented

- Exact row DP with a quadratic-state reference and residue-class sliding-minimum implementation.
- Physically legal full integer output alphabet; coarse-lattice outputs are preferred.
- Exact protected entries and a uniform two-dimensional prefix-error bound.
- Exact O(W) coarse-only row feasibility diagnostic.
- Correctness tests, synthetic payload probes, saved source/reconstruction arrays.

The recorded objective is off-lattice count plus a squared-prefix tie-break, not actual compressed bytes. Full-field corridor refinement is derived in the notes but **not implemented**.

## Run

The recorded environment uses Python 3.13.5 with the listed NumPy and Numba versions (see results/environment.json). Other Python/library combinations were not validated:

```bash
python -m pip install -r requirements.txt
python test_and_screen.py
python test_coarse_feasibility.py
python scale_probe.py
```

These scripts overwrite the corresponding result files in this folder. Copy the artifact before re-running if the recorded evidence must remain unchanged. First use of Numba may compile kernels. The scale screen runs a separate exact all-rectangle audit, in addition to quantization.

Simple use on a valid integer field:

```python
import sys
import numpy as np
sys.path.insert(0, 'src')
from corridor import reconstruct, rectangle_max

x = np.load('source.npy').astype(np.int64)
epsilon = 100
# NoData values must first be handled according to the caller's data contract.
y, info = reconstruct(x, band=epsilon // 4, step=20, cap=10000)
assert rectangle_max(y - x) <= epsilon
np.save('reconstruction.npy', y)
```

The function constructs a reconstruction; it is not a self-contained file-format encoder. Geo metadata, mask semantics, framing, checksums and cold independent decoding still need integration with the project's common carrier before any claim about complete scientific streams.

## Evidence

`results/tests.json`: 1500 fast/reference checks, 500 independent exhaustive row checks, 300 complete-field checks.

`results/coarse_feasibility_tests.json`: 1000 exact-feasibility/DP agreement checks.

`results/scale_screen.json`: four **synthetic** 512x512 sources, two fixed parameter settings. The table reports compressed-array payloads only, compared with shuffled uint16 LZMA6 source payload. It is not a comparison with the four real source packets.

The checkerboard remains exactly unchanged at both settings. Its positive payload difference is representation-only; its negative difference exposes stream overhead. Do not report it as lossy-algorithm gain.

`history/source_only_fine`: earlier exploratory restriction allowing only the original source as the fine option; retained for provenance. The current method permits any legal integer fine output.

The exact native dependencies and controls in the original project have not been copied into this prototype. No claims about full codec reproducibility or publication readiness are made by this artifact.
