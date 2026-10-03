# From a fixed divisor to rate-selected coarse precision

## Target

Remove the empirical divisor from step selection while keeping the paper's
central result intact: exact remaining-row feasibility realizes a bounded
integer field with accurate sums for every future rectangle. The step should
optimize the bytes actually delivered at the prescribed error budget.

## Status

**COHERENT AFTER REFRAMING.** The exact object is the best step for the fixed
backward–forward constructor and lossless file encoder. A universal expression
q = epsilon/c is not implied by the theory. Complete finite search gives an
exact step optimum, including all 65536 steps supported by the existing
transport. The construction and packet decoder are unchanged.

## Invariant object

Fix a source X, range cap U, missing mask M, exact protected set P including M,
and rectangular error budget epsilon. Let F_epsilon(X,P) be the set of integer
fields Y in [0,U] that equal X on P, are zero at M, and satisfy

\[
 D_\square(X,Y):=\max_R\left|\sum_R(Y-X)\right|\le\varepsilon.
\]

Here R ranges over all nonempty axis-aligned rectangles. The rate objective is
the length of the **whole delivered file**, not the count of fine pixels.

## Assumptions and notation

* X has H rows and W columns; N = HW. Values are integers in [0,U].
* B = floor(epsilon/4). For the current executable implementation, epsilon is
  a nonnegative integer, B <= 10000 and U <= 32767; N <= 4096 squared.
  The mathematical construction allows arbitrary nonnegative integer caps.
* q is a positive integer coarse step. Transport-supported steps are 1..65536.
* A_q(X) is the deterministic backward–forward output at band B and step q.
  It chooses a coarse multiple whenever one has a valid remaining-row
  completion, with the existing nearest-zero and smaller-state tie rules.
* C_q(Y) is the unchanged complete RRF2 encoder. Its quotient/remainder arrays,
  masks, common configuration, geospatial metadata and integrity information
  are all paid. Candidate method metadata differs only in q.
* L_q(X) = 8 |C_q(A_q(X))|, in bits. The implementation uses bytes, which has
  the same minimizing step. Ordinary metadata already carries q.
* Q is a finite, nonempty candidate set. Selection ties choose the smaller q.
* m_q counts the nonzero remainders in A_q(X); m_P,q is the protected count.

## Strategy and derivation map

1. Use exact remaining-row feasibility to separate legality from coarse scale.
2. Recover the geometry-dependent fine count and its finite code bound.
3. Keep that bound distinct from actual lossless file size.
4. Minimize complete file length at fixed epsilon, over the chosen step family.
5. Prove exact large-step equivalence to accelerate a complete transport search.
6. Verify paid rates, source-free decoding, every rectangle and encoder cost.

## Main derivation

### 1. Legality is independent of the chosen coarse scale — proposition

For every q >= 1, the constructor has a successor inside its exact feasible
interval. Coarse precision is a preference among these successors, not a
restriction on the existence of a legal completion. Consequently

\[
 A_q(X)\in\mathcal F_\varepsilon(X,P)\qquad\text{for every }q\ge1.
\]

The global distortion certificate comes from B. For the prefix errors E,
every rectangle is a signed sum of four corner values, giving

\[
 D_\square(X,A_q(X))\le4\|E\|_\infty\le4B\le\varepsilon.
\]

Thus changing q changes the legal field and its coded rate without changing
the prescribed accuracy guarantee. There is no need to use q = epsilon/5 to
prove legality.

### 2. Geometry determines the fine count — exact identity

At an unprotected forward choice, the allowed prefix states form an integer
interval I_j = [l,h]. The corresponding feasible pixels form
J_j = [s,v], with s = t_j + l - a and v = t_j + h - a, using the paper's
preceding state a and source-adjusted increment t_j. The number of coarse
values in that interval is

\[
 \kappa_j(q)=\left\lfloor\frac vq\right\rfloor
             -\left\lfloor\frac{s-1}q\right\rfloor.
\]

The forward rule uses fine precision exactly when this count is zero:

\[
 m_q=m_{P,q}+\sum_{(i,j)\notin P}\mathbf1\{\kappa_j(q)=0\}.
\]

All intervals and states here belong to the trajectory constructed at q.
Reusing intervals from a different q silently changes the object being
optimized: earlier choices influence later prefix states and allowed pixels.

### 3. The finite code bound explains the tradeoff — achievable code bound

For q >= 2 and known N,U,q, put K_q = floor(U/q)+1. The existing enumerative
representation uses at most

\[
 \Phi(q,m_q)=\lceil N\log_2K_q\rceil
 +\lceil\log_2(N+1)\rceil
 +\left\lceil\log_2\binom N{m_q}\right\rceil
 +\lceil m_q\log_2(q-1)\rceil
\]

bits, plus separately encoded masks and metadata. At q = 1, m_q = 0 and only
the quotient rank is needed. A coarser alphabet lowers quotient cost; fine
positions and their nonzero remainders add cost. This is an achievable
enumerative code, not a bound on the particular LZMA packet's length.
LZMA additionally reacts to the spatial sequence and repetition of values.

There is no source-independent optimum supplied by this bound. For an exact
example, use N = 8, U = 3, any fixed budget, and protect all pixels. Then Y = X.
For q = 1,2,3,4, exact finite rank lengths are:

| Source field | q=1 | q=2 | q=3 | q=4 | Minimizing steps |
|---|---:|---:|---:|---:|---|
| Eight zeros | 16 | 12 | 12 | 4 | 4 |
| Eight threes | 16 | 12 | 12 | 17 | 2, 3 |

The optimal sets are disjoint despite identical dimensions, range, protection
and error budget. This counterexample concerns Phi, with q supplied to its
decoder; it is not asserted to be an LZMA counterexample. It rules out
deriving a universal epsilon-only optimum from the paper's coding bound.

### 4. Exact step optimization at a fixed rectangular budget — theorem

For any finite, nonempty Q define

\[
 q^*(X,\varepsilon;\mathcal Q)
 =\operatorname*{arg\,min}_{q\in\mathcal Q}(L_q(X),q),
 \qquad Y^*=A_{q^*}(X).
\]

The pair in the argmin means shortest file first, smaller step on equal size.
Then:

1. Y* is in F_epsilon(X,P).
2. Its complete rate equals min over q in Q of L_q(X).
3. If Q contains a reference step q0, its rate is at most L_q0(X).
4. For Q1 contained in Q2, the minimum rate for Q2 is no larger.
5. The ordinary packet is sufficient for source-free decoding; no candidate
   list, search history, source-dependent tables or extra correction is sent.

**Proof.** Statement 1 follows from the guarantee for every candidate.
Statements 2–4 follow from evaluating the same complete cost for each member
and taking its minimum. For 5, the unchanged packet signals q and contains
both losslessly encoded arrays and masks; decoding reconstructs Y = qZ+r.
The candidate search is entirely encoder-side. This proof uses neither a
source-distribution model nor a high-resolution approximation.

The distinction from unrestricted rate–distortion optimization is explicit:

\[
 \min_{\substack{Y\in\mathcal F_\varepsilon(X,P)\\q\in\mathcal Q}}
      8|C_q(Y)|
 \ \le\ \min_{q\in\mathcal Q}8|C_q(A_q(X))|.
\]

We solve the right-hand **step optimization exactly**. Equality with the
left-hand search over every legal field is not proved. The one-pass greedy
constructor is not relabelled as a globally rate-optimal field constructor.

### 5. Exact reduction for all supported steps — proposition

For q > U the only coarse value in [0,U] is zero. All those steps give the
same output Y_infinity under the fixed rule. At each transition either zero
is feasible and is chosen, or no coarse value is feasible and the same
nearest-zero prefix state is chosen. Inductively, preceding-row states,
backward intervals and subsequent decisions are identical. Protected outputs
are independent of q as well.

Also floor(Y_infinity/q) = 0 and Y_infinity mod q = Y_infinity. Thus all array
and mask streams, the reconstruction digest and every fixed header size agree.
Only the compressed metadata length can vary with the decimal spelling of q.
For these steps the **exact full cost** is

\[
 L_q(X)=8\bigl(K_\infty+
    |\operatorname{zlib}(\operatorname{JSON}(\mathrm{meta}_q))|\bigr),
\]

where K_infinity is the common byte count outside metadata, including the
fixed-size checksum. Its value changes when metadata changes, but its length
does not. Metadata is evaluated for every large step, without assuming
monotonic size or using q=U+1 as an unproved representative.

For Q = {1,...,65536} the implementation therefore needs U+1 constructions
and complete array encodings, followed by 65535-U additional metadata cost
evaluations. This gives an exact optimum over the **whole supported step
domain** for this constructor and codec. For cap 100 it uses 101 full trials.
For cap 10000, full search still needs 10001 trials; a finite candidate mode
is available with its narrower optimum scope stated explicitly.

### 6. The four-corner factor is sharp — separate certificate proposition

For any integer B >= 1, the coefficient four is attained with binary source
and output pixels. Form a 3B-by-3 error field D consisting of B copies of
row (1,-1,-1), followed by 2B copies of (-1,1,1). Let X = max(-D,0) and
Y = max(D,0), elementwise. Both fields lie in {0,1}, so they obey every cap
U >= 1. Their prefix error is g_i times (1,0,-1), where g_i is the cumulative
row sign and ranges from -B to B. Hence every prefix has magnitude at most B.
The last 2B rows and last two columns have total error 4B.

This proves sharpness of the generic prefix certificate even with the pixel
range enforced. It does not claim that the algorithm attains its worst case
on the benchmark fields. `tests/test_prefix_certificate.py` checks the
construction and exact rectangle maximum for five bands.

## Verification and measured evidence

Frozen protocol: `docs/STEP_SELECTION_PROTOCOL_20261004.md`. All raw sources,
code and earlier measurements are hashed before new execution. The experiment
and its first independent replay completed before the subsequent user-requested
manuscript narrative revision. The original fixed-q comparisons stay unchanged.

`results/step_selection_20261004/report.json` records 16 successful selections,
872 full constructions/encodings, 524352 exact candidate lengths, and 16
source-free process decodes with exact all-rectangle audits. A second set of
16 decodes in `replay/validation.json` reproduces every saved winner's audit
and the aggregate report. No GPU or new source acquisition was used.

Each row below aggregates four existing 512-by-512 locations. Both the fixed
and selected files use identical metadata schemas. Gains are against the
original fixed step, not against an external codec or a newly acquired holdout.

| Quantity / budget | Fixed rate (bpp) | Selected rate (bpp) | Reduction | Chosen steps |
|---|---:|---:|---:|---|
| Built area / 100 | 5.7946 | 4.9232 | 15.04% | 50, 50, 50, 50 |
| Built area / 1000 | 3.5236 | 3.2312 | 8.30% | 333, 500, 500, 500 |
| Water / 100 | 0.3951 | 0.3872 | 1.99% | 11, 9, 33, 20 |
| Water / 1000 | 0.2076 | 0.2035 | 1.95% | 100, 100, 98, 100 |

Built area uses the eight existing predeclared steps. Water evaluates all
65536 supported steps exactly, using the equivalence reduction. Four of the
eight water cases have zero improvement; those cases remain in the report.
At budget 100 the water optimum varies markedly across locations despite
identical cap and budget, further illustrating the source-specific decision.

CPU encoder search averaged 1.20 seconds per built-area case (eight trials)
and 11.81 seconds per water case (complete supported domain). Their fixed-step
candidate times averaged 0.140 and 0.073 seconds respectively. These are warm
in-loop comparisons on the current local machine, not matched repeated timing
benchmarks. Exact audit and process-launch costs are outside selection timing.
The selection decoder is included in the search time. No unchanged linear-time
end-to-end encoder claim is made for exhaustive search.

## Remarks and manuscript use

The paper's strongest story remains **independent pixel tolerances can require
exact reconstruction; exact realizability enables a legal lossy field with
deterministic accuracy for every later rectangle in linear construction time**.
Rate-selected q is a short coding consequence of that result, not a second
headline. Fixed-q main comparisons and adaptive probe measurements remain
distinct. A short statement of the complete-file objective removes the
arbitrary ratio from the available selection mode without expanding the main
method into a large optimization section.

Classical entropy-constrained quantizer design also couples its objective to
the coded rate and optimizes numerically. Chou, Lookabaugh and Gray's algorithm
is an iterative, locally optimal design under its own assumptions; its theorem
does not establish the present step result. Primary source:
[Entropy-Constrained Vector Quantization, IEEE, 1989](https://web.stanford.edu/class/ee398a/handouts/papers/Chou%20-%20EC%20VQ.pdf).

## Boundaries and nonclaims

* No universal closed expression q = epsilon/c is derived.
* No equality with the optimum over all legal reconstructions is asserted.
* The enumerative bound and fine-pixel count do not replace actual file size.
* An eight-step optimum is labelled as eight-step, not complete-domain.
* The step optimum can depend on packet metadata and the fixed lossless coder.
* Extra encoder cost is paid; neither search history nor the source is sent.
* Original scan reanalysis is separated from the new adaptive encodes.
* No new benchmark-wide SOTA or award claim follows from these probes.

## Reproduction

From the full repository, with the existing LinewiseROI environment:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src:experiments \
  ../LinewiseROI/.venv/bin/python -m unittest tests.test_rate_selected_step tests.test_prefix_certificate
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src:experiments \
  ../LinewiseROI/.venv/bin/python experiments/replay_step_selection.py
```

The run script's original `freeze/run/replay` stages are preserved, including
the first replay against the pre-revision manuscript. Re-execution of new
experiments requires a new output directory and preflight, not overwriting
the saved evidence. The later artifact replay checks computation inputs and
earlier scan measurements while permitting the explicitly requested paper edit.

