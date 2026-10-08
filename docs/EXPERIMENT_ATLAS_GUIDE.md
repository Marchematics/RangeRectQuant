# Experimental figure collection

`../paper/figures/research/experiment_atlas.pdf`: seven pages, 68 panels. Each
page also has an individual vector PDF and 300-dpi PNG in that directory.

## Page captions and measurement scope

1. **Rate, step, protection and scale (4×4).** Row A: complete-file rates over
   eight budgets, forty built-area locations at three sizes and eight water
   locations. Gaps retain incomplete family coverage. Row B: each original
   holdout at eight divisors, for rate and fine percentage at both budgets.
   Dotted lines mark divisor five. Row C: four-city means at five protected
   fractions, showing rate, fine percentage, warm construction-plus-audit time
   and exact-value stream rate. Row D: London crops at budget 100 m² for
   construction, encoding, source-free decoding and whole-process memory.
   Construction measurements cover the proposed rule and exact row search.
   Warm times use three-repetition medians; protection panels average medians
   across cities. Rates include all complete-file fees and masked positions.

2. **Identical-field coding (2×4).** All forty new 512² locations, alphabetically
   ordered in batches of ten. Rows use budgets 100 and 1000 m². Each triplet
   stores exactly the same reconstructed field with direct 16-bit, byte-shuffled
   and split quotient/remainder LZMA streams. Complete rates include metadata
   and other fees. Decoded pixel hashes are checked before plotting.

3. **Precision details (4×4).** Columns: Cairo, Delhi, New York, Jakarta. Rows:
   complete rate, fine percentage, remainder rate and narrow-interval percentage.
   Both budgets and all eight divisors appear. Each metric row shares y-limits.
   Narrow intervals bound possible fine choices; they are not the measured fine
   frequency. Fine percentages use all 512² field positions. The default divisor
   remains five.

4. **Closest constructions (2×4).** All 56 decoded files: four cities, seven
   constructions, two budgets. Top: largest absolute rectangle-sum error divided
   by budget, on a log axis. Bottom: complete bits/pixel, on a zero-based linear
   axis. Crosses mark integer, range or regional failures. A smaller marked file
   remains ineligible. Only the eight proposed files meet all requirements. The
   construction key is printed on the same page.

5. **Water occurrence (2×4).** All eight native 512² locations and eight budgets.
   Curves compare proposed files with each location's smallest eligible external
   file. Budgets are percentage-point sums; zero occurrence is valid. Panels use
   independent y-axes to retain their different native entropies. Masks and
   metadata are paid. Tight-budget losses and the overhead crossover remain.

6. **Scaling (2×4).** London crops, 256² through 4096², at budgets 100 and
   1000 m². Columns: construction, complete encoding, source-free decoding and
   whole-process memory. Apple M4/16 GB, single thread, three warm repetitions.
   Construction measurements cover the proposed rule and exact row search.
   Exact search's 4096²/1000 m² worker reaches the 180-second timeout; no endpoint
   is supplied for any metric from that worker. Process memory includes arrays,
   coding and JIT; it differs from the theorem's additional row workspace.

7. **Field mechanism (1×4).** Cairo, budget 1000 m², coarse step 200 m². Source
   built area, bounded global prefix error, allowed-state counts and fine pixels
   are separated. All panels use the same saved 512² field. Every fine position
   has fewer than 200 allowed states. No synthetic spatial values are added.

Built-area source: European Commission, Global Human Settlement Layer,
GHS-BUILT-S R2023A, 2020 epoch (Pesaresi and Politis, 2023). Water source:
European Commission Joint Research Centre, Global Surface Water, 1984–2024
occurrence (Pekel et al., *Nature*, 2016). Full references are in the article
and `../references.bib`.

Reproduce with `../plotting/make_experiment_atlas.py`. Its receipt records all
input/output SHA256 hashes, plotting sources and exact displayed values.
