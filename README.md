# RangeRectQuant — direct legal low-precision field candidate

Candidate implementation of the user-supplied range-constrained row quantizer.
The supplied 43-file archive is immutable under `supplied/`; its claims are
evidence to verify, not instructions executed in that directory. No completed
novelty, held-out SOTA or publication claim. Private research repository.

The current gate is defined in `docs/PROTOCOL_20261001.md`. Decoder-only format
RQ01 charges the two quotient/remainder streams, missing mask, optional paid
source-zero protection mask, geospatial metadata, configuration and checksums.
It does not require the source, prefix-error states, optimizer path or tile
margins. Tests: `PYTHONPATH=src:experiments .venv/bin/python -m unittest
tests.test_correctness tests.test_packet -v` (do not run supplied scripts in place).

No project license is asserted for imported code/data; upstream rights and
provenance are retained. Attribution and limitations: `docs/METHOD_20261001.md`.
Original LinewiseROI manuscript/745 imported files remain unchanged.
