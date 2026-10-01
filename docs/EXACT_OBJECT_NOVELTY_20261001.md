# Exact-object 查新：经典算法重合与尚缺的研究贡献

2026-10-01。只读secondary Codex审查，不是人类peer review或完整查新
认证；skill要求的gpt-5.5不可用，实际inherited Codex fallback。公开
摘要与访问范围留在此处，完整AI交互private不入Git/ZIP。provisional
algorithmic novelty **3/10 / PROCEED WITH CAUTION** 是审查意见，不是客观
评分。未定位完全同一published oracle，不等于absence proof。

## 精确对象，而不是只比较术语

固定incoming prefix row u，delta_j=u_j-u_(j-1)，t_j=x_j-delta_j，
状态a,b∈[-B,B]，合法重建y_j=t_j+b-a∈[0,U]。当前row目标是lex
`(off-lattice count, sum b²)`；保护位置强制y=x。这个具体目标/联合
服务可以有应用价值，但一般有限状态最短路不因换目标就成为新范式。

设 `I_b=[t_j+b-U,t_j+b] intersect [-B,B]`。未保护转移可写成：

```text
D_j(b) = (0,b²) + min_lex(
    min_{a in I_b, a == t_j+b mod q} D_(j-1)(a),
    (1,0) + min_{a in I_b} D_(j-1)(a))
```

第二分支含粗化前驱无妨，因为其零罚分支支配它。随b增加窗口端点
单调；按余数拆分后也是滑动最小值。**我们的映射推理**：min queue
只需全序，统一加destination cost保序，所以lex pair不带来新的组合
加速原理。复杂度O(W(2B+1))对数值B是pseudopolynomial。

## 最强明确前例与访问范围

|primary source|明确重合 / 不应外推|实际访问|
|---|---|---|
|[Gribanov–Shumilov–Malyshev 2022](https://arxiv.org/html/2209.04812v2)|minimum queue、linear sliding-min convolution及按余数分解的bounded-knapsack DP有明确经典描述；不是说其完整应用等同本服务|root与副审相关§§2.1/3.1/4；没有读其所有证明|
|[Lemire streaming maximum/minimum](https://arxiv.org/html/cs/0610046v5)|amortized-linear monotone deque已有；不能把deque本身当原创|副审相关全文methods|
|[Pferschy 1999](https://doi.org/10.1007/S006070050042)|更早bounded-knapsack DP改进；不据此把具体deque实现归给该文|publisher abstract，未读full proof|
|[Kämpke constrained quantization 2003](https://www.sciencedirect.com/science/article/abs/pii/S016516840300104X)|value/structure constraints和finite-horizon DP已有；尚未证明同一周期异常目标|abstract/introduction/section synopsis，非完整算法|
|[Doerr global roundings 2004](https://www.sciencedirect.com/science/article/pii/S0020019004002194)|每个subinterval低discrepancy的整数rounding已有；不同floor/ceil设置|publisher abstract；author PDF读取失败|
|[Knuth two-way rounding](https://arxiv.org/abs/math/9504228)|simultaneous partial-sum constraints / integral rounding via flow已有；不称完全同问题|primary abstract，非full proof|
|[Lyu–Wang 2020](https://arxiv.org/html/2005.08487v1)|2D bounded state/mixed difference/prefix结构是直接前例；其greedy alphabet条件不是所有非因果in-box量化不可能性|相关§§2.2/2.4|
|[Asano et al. 2003](https://dspace.jaist.ac.jp/dspace/bitstream/10119/4906/1/B3022.pdf)|matrix/regional discrepancy rounding已有；本候选不解决经典all-rectangle全局最优|前轮method副审相关§§1–4；root未读full proof，本轮fresh open失败，不声称再次独立读过|

Gribanov文使用two-min-stack queue，并非和我们deque逐行同代码；原文
对Pferschy历史归属也有限定。我们的结论是**基础primitive与加速原理
重合**，不是宣称完全duplicate或把有限检索当全领域排重证明。

## 近期交集：动机可以保留，“首次”不能自动保留

|近期/邻近primary|与候选的交集/区别|访问|
|---|---|---|
|[Krahmer–Lupoli Sep2026](https://arxiv.org/html/2609.17276v1)|torus rank-one sampling trajectory接1DΣΔ；其lattice是采样几何，不是本候选output mod q|root与副审相关§4.1|
|[Joy–Krahmer–Lupoli May2026](https://arxiv.org/html/2605.17127v1)|causal one-bitΣΔ轨迹稳定性，非minimum-exception DP|副审相关primary方法|
|[Ugalde–Armour ICML2026](https://proceedings.mlr.press/v306/ugalde26a.html)|physics-aligned geometry/quantization，不能凭摘要精确排重|official abstract；full PDF fetch失败|
|[DiscQuant COLT2025](https://proceedings.mlr.press/v291/chee25a.html)|discrepancy neural-weight quantization，不是上行ICML文章|official abstract|
|[TOPIQ Aug2026](https://arxiv.org/html/2608.26912v1)|post-hoc spatial QoI prediction是统计预测，不是本服务deterministic preservation|前轮相关方法全文|
|[QPET VLDB2025](https://www.vldb.org/pvldb/vol18/p2440-liang.pdf)|QoI预算/付费correction已有；本路线直接构造joint合法场|前轮相关§§4–5|

有界状态稳定性、物理合法性、post-hoc查询与真实收费的交集仍值得研究，
但必须证明一个**经典构造之外的重要差异**。近期paper不能作为将成熟
primitive重新标成hot原创的理由；source-clipping失败也不证明所有
noise-shaping都必须失败。

## 检索与当前否决

副审对 constrained quantization、sequence/matrix rounding、residue/
sliding-min acceleration各≥3种query，另覆盖2026-04-01至10-01近期
检索及bounded official venue检查；非所有ICLR/NeurIPS/ICML exhaustive
audit。DBLP成功；HF paper_search connector报 `Tool paper_search not
found`，这是工具失败，不当空结果或没有相关文献证据。

副审要求的suffix-viable O(HW)控制现已完成：DP在同carrier的额外paid
收益仅0.54%/0.85%，两个必要性门均FAIL（见新结果文档）。因此不能
再以低fine计数、conditional exactness、deque加速或弱myopic greedy
失败支撑重要创新。joint合法服务成绩保留，但没有global fine/byte
optimality、普适sparsity、holdout或SOTA证据。

**下一道研究门是重要剩余瓶颈+非经典贡献+可证伪预言，之后才是新
留出验证。** 对简单控制没有实质分离时，不增加工程复杂度来包装论文。
