# Construction mechanisms and protected measurements

The frozen comparisons are complete: 56 closest-mechanism files and 40 protected-sample files were decoded in a separate process and audited. No execution exception occurred. Exactly eight closest-mechanism files meet the joint contract, all from RangeRectQuant. All forty protected-sample files meet it.

The published sigma–delta mechanism uses its prescribed expanded alphabet and exact rational arithmetic. Its cumulative-error bound survives: each rectangular error is below the chosen regional budget. Some outputs leave the physical range, and many outputs are fractional. Clipping restores the range and produces large regional errors. Nearest-integer roundback after clipping leaves these errors. Restricting the alphabet inside the feedback loop also exceeds the regional budget in these tested settings. Independently rounded prefix tables have bounded regional discrepancy before inverse-differenced pixels are clipped; clipping again destroys that control.

These tests isolate quantization constructions. They do not reproduce or make a claim about Lyu and Wang's subsequent total-variation image decoder. Their mechanism serves as the exact published bounded-state reference. Invalid reconstructions remain available as complete paid files and are not treated as legal competitors.

The protected sweep uses nested random sets selected with seed 20261002. Missing samples are always exact; arbitrary protected nonzero samples are preserved separately. The transmitted protected bitmap is paid in every file. The results verify every protected value, the full output range and the exact maximum rectangular error at both budgets. They also verify the fine-interval lemma at every unprotected pixel. Fine values forced by protected samples are recorded separately.

Sources and actual outputs:
- `results/closest_mechanism_20261002/{ledger,report}.json`
- `results/protected_sweep_20261002/{ledger,report}.json`
- `.aris/evidence/expanded_20261002/{closest,protected}/`: all 96 complete packets
- `paper/figures/research/`: saved-data figures and SHA-256 provenance

Construction times in the original single-pass sweep include first-call compilation. They are retained as measured, not interpreted as a protected-fraction speed trend. A uniformly warmed repeated measurement will supply that comparison.

The forty-location GHS frontier is a separate running experiment. This note reports no completed expanded-frontier numerical result.

The structural statements in `docs/STRUCTURAL_RESULTS_20261002.md` passed an independent automated proof review. It checked real/integer hypotheses, masks and protected samples, the fine-width lemma, and the ideal entropy/enumerative bound. The minimax is over all admissible input–output pairs. The entropy bound does not predict actual LZMA bytes; component-byte evidence supplies that interpretation.
