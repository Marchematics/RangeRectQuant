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

## Completed development gate (2026-10-01)

All eight preassigned nontrivial services pass. Against the named stronger
prior including paid conditional Haar, complete storage falls **30.79% / 56.14%**
at the two engineering budgets. This is not a held-out or SOTA result.
See `docs/RESULTS_20261001.md`, `docs/REVIEW_AND_NEXT_GATE_20261001.md`, and
`docs/REPRODUCIBILITY_20261001.md`; raw packets, full decoded fields, fees,
failures and fresh replay are under `results/`. The initial sweep is unchanged;
no refinement was added after it passed. No GPU was used.

## Stronger simple-control gate (2026-10-01)

The subsequently frozen suffix-viable **O(HW)** greedy control achieves almost
all the paid benefit. In a matched QF01 carrier, exact row DP adds only
**0.54% / 0.85%**, failing both preregistered ≥10% necessity gates. This does
not invalidate the original RQ01 gains, but rules out their use as evidence
that expensive DP is necessary. Its exact conditional objective remains valid.

Current decision and complete32-packet evidence:
`docs/VIABLE_GREEDY_CONTROL_RESULTS_20261001.md`,
`docs/EXACT_OBJECT_NOVELTY_20261001.md`, and `findings.md`.
The earlier post-A/B next-gate document is historical. The failed necessity
test favors the lightweight realization; it does not reject the joint-contract
method family. Innovation need not replace every classical primitive.
No new sources, refinement or held-out/SOTA claim. QF01 decoder smoke tests:
`PYTHONPATH=.:src:experiments .venv/bin/python -m unittest
tests.test_viable_greedy tests.test_correctness tests.test_packet -v`.

## Current research direction

Proceed with **direct, range-aware coordinated quantization for unknown
rectangle queries**, using suffix-viable O(HW) as the main realization and
conditional exact DP as its oracle/control. The contribution is the joint
service/construction/paid-rate tradeoff, not invention of DP or four corners.
See `docs/RESEARCH_POSITION_20261001.md` for the precise literature delta.

The completed120-stream recompression diagnostic establishes a usage boundary:
each save is locally legal, but the original-source budget does not compose.
The observed violation stabilizes; it does not invalidate single-pass gains.
It remains a caveat, not a new method pivot. Results and independent checks:
`docs/RECOMPRESSION_DIAGNOSTIC_RESULTS_20261001.md`.

New-geography evaluation is specified in `docs/HOLDOUT_PROTOCOL_20261001.md`
and `integration/heldout_assets_20261001.json`: fixed Cairo/Delhi/New York/
Jakarta native windows, unchanged method parameters, full strong-control pool.
Acquisition manifests and experiment results determine the actual run status;
the existence of this protocol alone is not a completed held-out result.

## Four-new-geography result (2026-10-01)

The fixed Cairo/Delhi/New York/Jakarta experiment is now complete: **180 paid
streams and cold source-free full decodes, zero exceptions**. All eight primary
services are nontrivial and jointly legal; each budget wins4/4 against the
smallest legal external-control stream, reducing paid storage **31.28%/55.77%**.
This is actual geographical-transfer evidence with unchanged parameters.
See `docs/HOLDOUT_RESULTS_20261001.md` and `docs/METHOD_MAIN_20261001.md`.
The fixed pool includes native SZ3/QPET/MGARD and conditional Haar; broader
codec-frontier claims remain a separate evaluation, not an excuse to discount
the measured result.
