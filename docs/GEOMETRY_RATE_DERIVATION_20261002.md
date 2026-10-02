# Feasible geometry to a finite-block code

Let N=HW, q>=2, and use the existing integer input, range, mask and protected
set assumptions. At each unprotected forward step let I=[l,h] intersect Z be
the nonempty feasible state interval, and J=[s,v] intersect Z the feasible pixel
interval, where s=t+l-a and v=t+h-a. Set

    kappa = floor(v/q) - floor((s-1)/q).

The coarse-first rule produces a nonzero remainder exactly when kappa=0.
Protected pixels contribute a nonzero remainder exactly when their source
value is not divisible by q. Thus, with m_P that protected count,

    m = m_P + sum_unprotected 1{kappa=0}
      <= m_P + sum_unprotected 1{h-l+1<q}.

The count bound needs the protected term; the review's proposed expression
without it is false for exact protected values outside the coarse alphabet.

For M=2B+1, the interval length also has the exact decomposition

    |I| = M - max(0,L_j+B,a-t+B)
            - max(0,B-H_j,B-a-U+t).

The two deficits identify how remaining-row restrictions and current range
constraints consume prefix-state width. Narrow intervals can still contain a
coarse value; kappa distinguishes their actual residue coverage. This is an
instance certificate, not an input-independent bound on exception density.

Let Q=floor(U/q)+1. A lossless code for the constructed field, with N,U,q known
to its decoder, uses at most

    ceil(N log2 Q) + ceil(log2(N+1))
    + ceil(log2 binom(N,m)) + ceil(m log2(q-1))

bits, excluding the separately counted metadata/masks. Encode the quotient
vector by its base-Q rank, m as one of N+1 values, exception positions by their
rank among binom(N,m) subsets, and nonzero remainders by their base-(q-1) rank.
Counts equal to one consume zero bits. Decoding reverses those finite ranks.
No independence or source-distribution hypothesis is used.

Consequently the fractional rate is at most log2 Q+h2(m/N)+(m/N)log2(q-1),
plus at most four rounding/count terms divided by N (the count term is
ceil(log2(N+1)), and three other ceilings cost less than three bits).
For a width-only upper bound eta=(m_P+N_narrow)/N, do NOT blindly substitute
eta into binary entropy: the monotone envelope uses
min(eta,(q-1)/q) in h2(r)+r log2(q-1). q=1 has m=0 and only the quotient rank.
This establishes an achievable representation bound, not an LZMA upper bound.
