# Expanded study: reproduce and inspect

## Existing evidence

The private repository contains the complete code, native cropped sources,
fixed metadata selection, attempt ledgers, source-free decoder logs, exact
region audits and failed configurations. GitHub release assets additionally
hold every original paid file and complete official source-product downloads.
Extract the source ZIP and paid-file ZIPs into one parent directory, preserving
`RangeRectQuant/.aris/evidence/expanded_20261002/` paths. The source ZIP
also contains the small sibling `LinewiseROI/experiments` dependency set;
it contains no virtual environment, credential store or Git database.

The paper compiles from `RangeRectQuant/paper` with the existing official
class and saved figure PDFs:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Independent decoding

Use Python 3.12 with NumPy2.3.5, Numba0.65.1 and Pillow12.3.0 for scientific
files and tests. Plot regeneration additionally uses Matplotlib3.10.8.
Choose a new output filename; decoding refuses overwrite:

```sh
cd RangeRectQuant
export PYTHONPATH=".:src:experiments:../LinewiseROI/experiments"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python experiments/decode_delivered.py \
 .aris/evidence/expanded_20261002/frontier/london-256/london-256-00-RangeRectQuant.packet \
 /tmp/london-decoded-new.npz
```

The output contains `y`, `mask`, `protected`, and file metadata. For rational
mechanism controls, `y` is the integer numerator and metadata `denominator`
supplies its denominator. Ordinary RRQ and native fields have denominator1.
No source is passed to this CLI. Complete reference files with native payloads
also require the matching scientific codec runtime, configured explicitly:

```sh
export DCC_NATIVE_PYTHON=/your/python-with-pysz
export DCC_NATIVE_MGARD_DRIVER=/your/native-mgard-driver
export DCC_QPET_API_V2_DRIVER=/your/native-qpet-api-v2-driver
```

The recorded run used pysz1.0.3, MGARD1.6.0 and QPET commit
5d17cb1647caf001bd7355c617856c72c4b6475e, on macOS arm64. Driver sources
and original build receipts are included. Build the upstream dependencies in
your environment; the receipts identify exact sources, commands and binary
hashes. The native binaries and Python environment are not an automatically
portable installation.

## Tests, figures, and original bindings

```sh
python -W error::ResourceWarning -m unittest discover -s tests -v
python paper/plotting/make_research_figures.py frontier mechanism closest water scaling protected
python paper/plotting/make_research_tables.py
(cd paper && python notes/check_manuscript.py)
```

The supplied-source import manifest and original acquisition records are
included. `validate_expanded_delivery.py` verifies all paid-byte accounting,
checksums, fixed-input hashes, exact recorded eligibility and external-winner
selection. Its original historical/runtime binding check intentionally uses
the recorded local absolute paths and all745 earlier originals. A new-machine
portable decode is separate from passing those original environment bindings;
do not edit old preflight records to imitate their original PASS.

Budgets, locations, coarse-step rules and native grids were fixed before their
reported runs. The complete first acquisition failures and metadata-only
repairs are retained. Warm protected timings use the already delivered fields.
The five successful native failure replays are separate files and do not
replace the original22 failure cells. No GPU was used.
