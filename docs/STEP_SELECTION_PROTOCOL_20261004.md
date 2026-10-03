# Rate-selected quantization step: fixed validation protocol

## Target and invariant

Replace the empirical divisor by minimization of complete RRF2 file length at
a fixed rectangular error budget. The backward–forward constructor, packet
format and decoder remain unchanged. Each candidate keeps the same source,
range, masks, geospatial metadata and budget. The selected step is already
signalled in the ordinary packet. All original paper results remain fixed-q
results; this experiment produces a separate adaptive encoder result.

The optimum concerns the deterministic constructor and this lossless coder.
It does not assert minimization over every legal reconstruction. Complete
files, including metadata and both integrity digests, are the rate objective.
Fine-pixel count and the finite enumerative code bound are explanatory quantities.

## Theory checks

1. Every positive step has the existing joint guarantee. Choosing among them
   preserves it, for a source-dependent choice as well as a fixed choice.
2. Evaluate every candidate's complete length and break ties toward smaller q.
   This is the exact step optimum in the evaluated family. Inclusion of the
   old step gives a no-rate-increase guarantee; nested sets obey the same rule.
3. For q greater than the value cap U, the only coarse value is zero. All such
   candidates follow one construction path and encode identical quotient,
   remainder and mask streams. Evaluate their compressed metadata separately:
   decimal step strings can change its size. This reduction is exact, with no
   unproved pruning or assumption of a smooth/unimodal rate curve.
4. A small exact protected-field counterexample distinguishes source-specific
   step selection from a universal epsilon-only optimum for the enumerative
   code bound. It is not presented as a proof about LZMA sizes.

## Sources and candidates, chosen before this new experiment

All fields are existing native 512-by-512 windows. No new acquisitions,
resampling, crop selection, source fitting or GPU computation is used.

* Built area: the four rows of `data/heldout_20261001/manifest.json`, in their
  existing order (Cairo, Delhi, New York, Jakarta), cap 10000. At budgets 100
  and 1000, use the eight existing divisor-scan steps from divisors
  16, 12, 8, 6, 5, 4, 3, 2. Report an exact optimum within these eight choices.
  These are previously studied geographic holdouts, not newly untouched data.
* Water occurrence: the first four rows of the existing
  `data/water_20261002/manifest_v2.json` (London, Chicago, Hanoi, Buenos Aires),
  cap 100. At the same two budgets, evaluate every transport-valid integer
  step 1 through 65536. The exact large-step reduction needs 101 complete
  constructions/encodings per field and 65435 additional metadata evaluations.
  Report an exact step optimum over the entire supported transport domain.

Expected totals: 16 selections; 872 complete constructions/encodings;
524352 candidate lengths (64 built-area plus 8 times 65536 water candidates);
16 independent process decodes and exact all-rectangle audits of winners.
The in-process selection decoder is an additional consistency check.

## Paid rate, legality and timing

Use one common method metadata dictionary per case with `family`, `epsilon`
and `quantization_step`, without a divisor or a search history. This isolates
the step decision from the previous scan's differently sized configuration.
Compare selected bytes with the old step **re-encoded under this same schema**:
max(1, floor(epsilon/5)) for built area, capped at 100 for water. No mixed-schema
byte comparison is used for a new adaptive gain.

Record each constructed candidate's complete bytes, component lengths,
fine/changed counts, maximum prefix error and construction-plus-encoding time.
Store the large-step metadata-length histogram and winning step. Save every
winner packet, checksum, decoder output metadata and exact rectangle maximum.
Accept a winner only if its integer range, missing mask, protected values and
rectangle budget all pass. Store exceptions as failures and do not replace
them with a new crop or step set.

Warm the constructor on a tiny field before timing. Report wall-clock encoder
search cost and the in-loop time of the fixed-step candidate separately.
Search increases encoder cost; it does not alter the source-free decoder.
Store only winner packets, not redundant trial files.

## Saved-result reanalysis and completion criteria

Separately summarize all 128 original step-scan JSON records: development and
original geographic holdouts, two budgets, eight divisors. Label this as
reanalysis of earlier measurements and keep their files unchanged. Report
full-file minimizers and the fixed-divisor-five comparison within each old
metadata schema. Do not call this a newly executed adaptive experiment.

Completion requires all expected selections and audits, fee accounting,
argmin/tie checks, unchanged frozen inputs, all repository unit tests, and a
replay that decodes the saved winners and regenerates aggregate statistics.
Freeze source/code hashes before running. The final report includes every
case, including zero gains or failures. The canonical manuscript is unchanged
by this theory/encoder experiment and can later incorporate verified evidence.

