# Regional accuracy beyond four maps

## Frozen question and parameters

The primary question is whether the backward–forward construction delivers a smaller complete file across new geographic locations, resolutions and regional error budgets. The supporting question is why physical range constraints must enter the construction.

Forty new city locations cover six geographic groups. Coordinates come from the GeoNames cities15000 dump (CC-BY-4.0, credited to GeoNames), selected using the named city, country and largest matching population. The asset manifest records exact identifiers, coordinates and the dump hash. Selection precedes pixel downloads. The previous eight locations remain development/earlier evidence and are not counted among the forty. These forty city-centered locations are a geographically varied sample, not a random global sample.

Use native GHS-BUILT-S R2023A E2020 100 m data, integer built area in [0,10000] square metres. The downloaded tile must have the expected Mollweide grid, uint16 type and NoData=65535. Select a 1024-square window using the nominal tile grid in the manifest. If a center is too close to the nominal tile edge, clamp it using coordinates alone. All smaller windows are centered native crops of this window. Report 256, 512 and 1024 square sizes separately; nested sizes are not independent locations. Transmit and preserve the missing mask. No resizing, interpolation, blank-window removal or value-dependent replacement is allowed.

Acquisition amendment, before any expanded method encoding: thirteen official files trim outer NoData strips and have smaller dimensions than the nominal 10000-square tile. Record actual header dimensions and affine transforms. Require grid-aligned trimming contained in the nominal tile. Read exactly the frozen geographic footprint using integer native-window offsets, padding absent coverage with NoData. Preserve the first partial manifest and all twenty-seven successful sources; a separately named amended manifest records repaired acquisitions. This header-only correction does not change any city, budget or geographic footprint.

Budgets are 25, 50, 100, 250, 500, 1000, 2500 and 5000 square metres. Set B=floor(epsilon/4) and q=max(1,floor(epsilon/5)). These include the previous fixed q=20 and q=200 settings. Choose no parameters from the new pixels.

## Complete-file frontier

Run RangeRectQuant at all eight budgets. Compare the already frozen 38 native/control configurations for integer LZMA, lossless JPEG2000, SZ3, MGARD and QPET, without changing their algorithms or pointwise bounds. Reuse each baseline file across budgets only after auditing its exact maximum rectangular error. Add the fixed-margin conditional 2-by-2 construction with m=floor(epsilon/4), plus m=0. New transport names and metadata must distinguish expanded parameters from the old frozen packet formats. Never redefine the meaning of a saved packet.

Every compared file pays for geometry, masks, parameters, integrity checks and compressed data. Decode every file in a source-free process. Audit range, masks, integer output and all rectangles. Report each baseline family's smallest qualifying file at each budget; mark absent qualifying files as unavailable. Report the external-best envelope as an empirical selection among this fixed grid, not a tuned universal codec. Keep exceptions and invalid attempts in the ledger. Plot complete bits per pixel against budget, with three resolution panels and a shared legend. Show city-wise paired reductions and win counts so an aggregate cannot hide expansion. Bootstrap intervals, if used, resample whole city locations; no uncertainty from fictitious training seeds.

## Closest construction stress test

Use the four existing geographic holdouts at budgets 100 and 1000, with no parameter search. Implement equation (2.1) and Proposition 2.1 of Lyu and Wang, *Sigma Delta quantization for images* (arXiv:2005.08487): d>=2, m=2^d-3, alphabet {-U/m,0,U/m,...,U,U+U/m}. Choose the smallest d giving 2U/m<=epsilon. Compute in exact integer numerator units with denominator m. Boundary states are zero and nearest-alphabet ties select the smaller value. This compares the published quantization mechanism; it does not reproduce its total-variation image decoder.

Compare the unmodified stable mechanism, output clipping, clipping plus nearest-integer roundback, and an in-loop alphabet projection to [0,U]. Also test independent prefix rounding at the RRQ step, inverse differencing, and clipping. Keep the unmodified rational outputs as exact numerator/denominator pairs. Report physical range violations, integer violations, exact worst rectangle error, full file bytes and joint valid rate. An invalid method is excluded from a legal frontier regardless of its file size. A negative result applies to the tested construction and parameterization, not to every possible sigma–delta algorithm.

## Constraint and scaling evidence

Select protected fractions 0, 0.1%, 1%, 5% and 10% of valid entries with a fixed seed, using nested sets. Repeat the same four existing holdouts at both budgets. Pay the protected bitmap separately from missingness. Report exactness, range, all-rectangle error, fine fraction, full size and construction time. Record feasible interval widths for unprotected entries; test that every unprotected fine entry has fewer than q admissible states.

Use a native 4096-square crop of the London tile, selected by metadata-only clamping, for scaling. Its smaller centered crops give 256 through 4096 square inputs. Distinguish construction-only time/workspace from the reference implementation's full-prefix audit and from lossless encoding. Warm JIT compilation outside timing. Report repeated time measurements, throughput and fresh-worker peak RSS. Dynamic-programming runs may be omitted at documented time/resource limits, preserving the attempted measurement. Do not extrapolate a skipped measurement.

## Decisions and evidence

No numerical win or strong-accept status is assumed. Freeze code before each new matrix, bind inputs and native runtimes by SHA-256, and retain decoded evidence. Use only completed runs in figures and the manuscript. Source data and old negative results remain unchanged. GPU use is zero for these experiments; any later GPU work stays within the user's one-GPU-per-project constraint.

Second-domain acquisition follows an independent product protocol after checking current official metadata and NoData semantics. It is not represented as completed by this document.

Sources: [GeoNames format/license](https://download.geonames.org/export/dump/readme.txt), [GHS product](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php), [published sigma–delta construction](https://arxiv.org/html/2005.08487v1).
