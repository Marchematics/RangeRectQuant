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
The earlier post-A/B next-gate document is historical; identify an important
nonclassical bottleneck surviving this control before expanding the method.
No new sources, refinement or held-out/SOTA claim. QF01 decoder smoke tests:
`PYTHONPATH=.:src:experiments .venv/bin/python -m unittest
tests.test_viable_greedy tests.test_correctness tests.test_packet -v`.
