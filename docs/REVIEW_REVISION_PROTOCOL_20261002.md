# Compression-mechanism revision: fixed experiments

The supplied review is an internal assessment, not an acceptance decision.
This revision tests the contribution through five compact blocks. Original
methods, files, budgets and results remain unchanged. No default step is tuned
using these measurements. All complete files include masks, configuration,
geospatial metadata, reconstruction digest and checksum. GPU use: zero.

1. Geometry and coding: characterize coarse choices exactly by the number of
   multiples in the feasible pixel interval. Include protected nonzero
   remainders. Derive a finite-block, lossless representation bound, distinct
   from the measured LZMA size. Test identities on small exhaustive intervals.
2. Representation: decode the 320 existing 512-square files from forty new
   locations and all eight budgets. Encode the identical field as raw uint16,
   byte-shuffled uint16 and split quotient/remainder. A fourth arm omits
   remainders and is audited as a different reconstruction, not a lossless
   representation of the same field.
3. Step sensitivity: four development and four original geographic holdouts,
   512-square, budgets100/1000, divisors16/12/8/6/5/4/3/2. Record complete size,
   both stream sizes, fine fraction, exact residue and width certificates.
   The original divisor5 remains the reported method.
4. Structured comparison: forty new 512-square windows, same two budgets.
   A capacity-constrained quadtree splits each parent total among four children,
   preserving total sum and the physical range. Use constant mass steps and
   steps scaled by valid-child counts, each at1/2/4/8/16/32/64/128/256/512.
   Compare shuffled pixel coding, quotient/remainder coding and reversible hierarchical sum-deviation
   coding; choose the smallest qualifying complete file, including all paid
   components. This is a newly implemented structural control, not a numerical
   reproduction of any cited paper's entire algorithm.
5. External density: four original geographic holdouts, 512-square. Add thirteen
   floating tolerances .25/.375/.625/.75/.875/1.5/2/3/6/8/12/24/32 to each of
   the seven original float configurations; add int64 SZ3 bounds1/2/4/8/16 to
   its three predictors. Original settings stay in the reference pool. Report
   the benefit of increasing float-tolerance density from4 to17, separately
   from the forty-location experiment.

Source-free processes receive file paths only. Rectangle eligibility uses a
rigorous prefix triage: maximum prefix error e certifies rejection for budgets
below e and acceptance for budgets at least4e. Ambiguous budgets receive exact
all-rectangle enumeration. The rejected witness and sufficient certificate are
labelled separately from an exact maximum. Identical decoded fields share the
same audit. Every failed encode remains in the attempt ledger. No unsuccessful
configuration is retroactively replaced or removed.

Expected new files:1280 representation +128 step +2400 hierarchy +424 native
attempts. Failed native attempts affect the completion count, not the plan.
The canonical article stays within DCC's ten-page total limit. Numerical claims
are added only after saved complete-file decoding and validation.
