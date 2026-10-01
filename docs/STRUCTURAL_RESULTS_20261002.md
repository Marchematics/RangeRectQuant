# From the guarantee to the representation

These statements supplement the backward–forward correctness proof. They do not assume a particular entropy coder.

## Independent pointwise certificates

Let the input and output lie in `[0,U]`, let protected entries be exact, and let `A` be the largest number of unprotected entries in an allowed rectangle. A certificate that uses only the independent inequalities `|Y-X| <= delta` must cover every pair satisfying those inequalities.

For real-valued entries its exact worst regional error is `A min(delta,U)`. For integer entries it is `A min(floor(delta),U)`, for nonnegative delta and integer U. Summing the individual bounds gives the upper bound. Set every unprotected source entry to zero and every unprotected output entry to the stated maximum admissible error. A rectangle attaining A gives equality. Protected entries remain zero and exact.

Consequently, for `0 <= delta <= U` in the real case and `A > 0`, certification of budget epsilon requires `delta <= epsilon/A`. For integer fields with `U >= 1` and `epsilon < A`, the certificate must have `floor(delta)=0`. Every covered reconstruction is then exact. This is a separation between independent pointwise and correlated-error certificates. A method can use additional information about correlated errors without being subject to this pointwise-only condition.

The proposed real-valued necessity cannot be copied unchanged into an integer theorem: delta=0.9 permits only zero integer error, even when epsilon/A is much smaller than 0.9. If A=0 or U=0, all regional errors are zero.

## Fine values identify narrow feasible intervals

At an unprotected position let `I_j=[l_j,h_j] intersect Z` be the nonempty interval of states admitting the current range constraint and a legal completion. Under the coarse-first policy, a fine pixel implies `h_j-l_j+1 < q`. Any q consecutive integers contain every residue modulo q. An interval containing at least q integers thus contains the coarse residue `a-t_j (mod q)`, and the policy selects it.

The converse is false: a shorter interval can still contain the target residue. Protected entries take a forced state and can have nonzero remainders even when the unprotected interval would be wide. The lemma counts only unprotected fine entries. For q=1 every integer is coarse.

## Representation and entropy

For a uniformly sampled output entry define `Z=floor(Y/q)`, `r=Y mod q`, and `rho=Pr[r!=0]`. For q>=2, the quotient has at most `Q=floor(U/q)+1` values. With `h2` denoting binary entropy, the joint zero-order entropy obeys

`H(Z,r) <= log2(Q) + h2(rho) + rho log2(q-1)`.

Use the nonzero-remainder indicator to split the remainder entropy: `H(r)=h2(rho)+rho H(r | r!=0)`. The nonzero remainder alphabet has q-1 members. Subadditivity and the quotient alphabet bound finish the proof. Define `0 log 0=0`. For q=1 the remainder is identically zero and `H(Y)<=log2(U+1)`.

For a finite field of n entries with exactly k nonzero remainders, there are at most `Q^n binomial(n,k) (q-1)^k` representations. An enumerative code uses the ceiling of the base-two logarithm of this count, plus a description of n, k, U, q and any mask and metadata. The inequality `log2 binomial(n,k)<=n h2(k/n)` gives the same leading bound. This is an available ideal code, not a bound on an LZMA file.

Quotient dominance is measured from actual component bytes. It does not follow from this entropy upper bound. The measured small remainder stream explains why reducing fine count substantially can have little effect on the full file.
