# Proof notes and implementation map

These notes derive the candidate's guarantees. They do not establish novelty over prior constrained quantization or matrix rounding. Unless otherwise stated, all arithmetic is exact integer arithmetic.

## Definitions

Let X be an H by W integer array in [0,U]. Let P be a set of protected entries. Define S as the two-dimensional prefix operator with zero row and column boundaries. For a proposed reconstruction Y, write E=S(Y-X). Let B be a nonnegative integer and q a positive integer.

The sufficient feasible set is

F_B(X)={Y integer: 0<=Y<=U, Y_P=X_P, ||S(Y-X)||_infinity<=B}.

This is a subset of the fields whose maximum absolute rectangle-sum error is at most 4B; the converse is not asserted. The optimization objective in the prototype is the number of sites whose output is not divisible by q. Squared prefix state is a secondary, lexicographic tie-break.

## Proposition 1: simultaneous rectangle guarantee

For any rectangle [a+1,b] x [c+1,d], its error equals E_bd-E_ad-E_bc+E_ac. If every prefix state has magnitude at most B, the absolute value is at most 4B. This covers all rectangles at once, including those selected after coding.

This elementary identity is classical. The scientific error contract also requires correct source units, full-field values, missing semantics, and exact/safely bounded arithmetic. The prototype does not implement the complete geospatial service carrier.

## Proposition 2: row recurrence and total feasibility

Fix the already encoded rows before i. Set u_j=E_(i-1,j) and u_0=0. Let a=E_(i,j-1), b=E_(i,j), d=u_j-u_(j-1). The mixed difference gives

y_j=x_j+b-a-d.

Thus a layered directed acyclic graph with states a,b in [-B,B] enumerates exactly all row reconstructions whose new prefix row lies in the band. An edge is admitted only if 0<=y_j<=U and the protected constraint holds.

The complete path b_j=u_j is feasible: its output is x_j at every site. The starting state is zero, and the prior prefix row is in the band by induction. Therefore every source in the contract admits a full feasible reconstruction, even when coarse-only reconstruction is impossible. This is a feasibility theorem, not a theorem that most outputs are coarse, nor a compression theorem.

Dynamic programming on this graph minimizes the pair (off-lattice count, sum_j b_j^2) exactly for this fixed incoming u. The entire first raster sweep is not globally optimal because its choices affect incoming states for later rows.

Implemented in src/corridor.py: row_reference and _row_fast. Checked by independent exhaustive output-sequence enumeration and full-field tests.

## Proposition 3: linear-in-band transition evaluation

For a fixed next state b, let t=x_j-d. Physical range gives the predecessor interval

I_b=[t+b-U,t+b] intersect [-B,B].

Coarse transitions additionally satisfy a=t+b (mod q). The next-state energy b^2 does not depend on the predecessor. Thus the minimum coarse predecessor is the lexicographic minimum old DP value in I_b within one residue class. The fine channel takes the minimum old value over all of I_b, then adds one to the first cost component.

Fine-channel duplication of a coarse edge cannot improve the solution: the same edge is available with strictly smaller primary cost in the coarse channel. It is therefore valid to minimize over the full legal integer alphabet in the fine channel without explicitly excluding coarse outputs.

On increasing b within a residue class, both interval endpoints move monotonically. A monotone deque visits each predecessor at most once on insertion and removal. The residue classes partition predecessors, so total coarse work per column is O(2B+1), even if q exceeds the state count. A second unrestricted deque gives O(2B+1) work for the fine channel. Protected sites instead use the single equality y=x.

The resulting row algorithm uses O(W(2B+1)) operations and O(W(2B+1)) backpointer space. The full first sweep costs O(HW(2B+1)), in addition to reading/storing the image. The dependence is on the numerical value B, not log B. The maximum-rectangle verifier is a separate O(H^2 W) procedure in the current orientation and is not included in the quantizer complexity.

## Proposition 4: exact coarse-only feasibility in O(W)

Assume first that the row has no protected sites. If all y_j are multiples of q, write sum_(l<=j)y_l=qK_j. Define v_j=sum_(l<=j)x_l-u_j. Then the prefix band is equivalent to

A_j=ceil((v_j-B)/q) <= K_j <= C_j=floor((v_j+B)/q).

Physical output bounds are equivalent to 0<=K_j-K_(j-1)<=Q=floor(U/q). If the reachable prior cumulative states form an integer interval [L,H], their successors form exactly [L,H+Q]. Intersecting with [A_j,C_j] gives the recurrence in the Chinese plan. The starting interval is [0,0]. By induction each reachable set is precisely the computed interval; a nonempty final interval gives a feasible backtrace. Any empty interval proves no coarse-only path exists under the fixed incoming u.

For a protected site, x_j must be divisible by q, and the reachable interval is shifted by the fixed increment x_j/q before intersection. Otherwise coarse-only feasibility fails.

Implemented in src/coarse_feasibility.py. One thousand randomized cases match whether the complete row DP has optimal off-lattice count zero. This diagnostic does not provide the squared-state-optimal coarse path and is not used to generate the recorded payload screens.

## Proposition 5: exact full-field corridor for a row replacement

Status: derived, not implemented or numerically tested in this artifact.

Given a feasible full Y, replace only row i. Let s_j=sum_(l<=j)(Y'_il-Y_il). For k<i, E_kj is unchanged. For all k>=i, it becomes E_kj+s_j. The intersection of the band inequalities over these suffix rows is exactly

-B-min_(k>=i)E_kj <= s_j <= B-max_(k>=i)E_kj.

The interval contains zero and has width at most 2B. All other requirements are local to the row: 0<=Y_ij+s_j-s_(j-1)<=U and equality at protected sites. No other constraints are needed to preserve this prefix-band feasible set.

A row DP on these variable state intervals minimizes the total field's off-lattice count conditional on the other rows. As a secondary target, the change in total prefix energy for column j is

2*s_j*sum_(k>=i)E_kj + (H-i+1)*s_j^2.

This again depends only on the next state. The same interval and residue-class minimum structure applies. As zero modification is feasible, the lexicographic global objective cannot increase when an exact row optimum is accepted. Strict improvement acceptance prevents equal-objective cycles. None of this yields global two-dimensional optimality or actual compressed-byte monotonicity.

A top-to-bottom sweep can precompute suffix extrema/sums at its start. Earlier row updates add the same accumulated shift to all remaining suffix rows at each column. Track this shift to update the current corridor in O(W) per row; the primary cost remains O(HWB) for a fixed sweep. This proposed fast implementation needs independent full-recomputation tests before use.

## Proposition 6: information-removal cap for fixed 2x2 margins

Fix a deterministic coding scheme whose decoded representation preserves the three margins in every disjoint 2x2 block, and whose remaining source scalar t differs from its decoded value by at most M. Given a complete bitstream C, the decoder determines the block margins and its reconstructed scalar. Each block has at most 2M+1 consistent source scalars. Thus at most (2M+1)^(N/4) source arrays can map to a fixed stream when dimensions are even and all blocks satisfy the premise. Consequently H(X|C)<=N/4*log2(2M+1) for any distribution supported on these sources.

This is an elementary preimage-counting bound, not an actual byte-gain bound against a particular baseline. Pinned/missing sites can reduce the preimage count. A decoder/coder that preserves fewer margins falls outside its premise. Do not infer that preserving three algebraic degrees of freedom preserves three quarters of the bytes.

## Tiny greedy failure

Take U=4, B=1, q=2, a fixed incoming prefix-error row u=[0,-1], and source row x=[1,4]. A local coarse rule choosing y_1=0 produces b_1=-1. At column 2, d=-1 and y_2=4+b_2-(-1)-(-1)=6+b_2. For any b_2 in [-1,1], y_2>=5, which violates the cap. The entire row remains feasible: [2,4] gives prefix row [1,0]. The incoming row can itself arise from source [0,1] reconstructed as [0,0].

This disproves that particular tie-breaking greedy rule. It does not exclude all look-ahead, interval-propagation, or globally informed greedy algorithms. The coarse-only interval algorithm above solves its own feasibility subproblem exactly.

## What is not established

No new geographic performance, no complete BA02 integration, no byte-optimal quantization, no global two-dimensional optimum, no universally sparse fine stream, no budget-independent runtime, no new lower bound for arbitrary rectangle-preserving compression, and no completed novelty claim. The attached plan identifies the experiments and algorithmic comparisons needed to evaluate those issues.
