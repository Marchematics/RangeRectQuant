# 证明/查新副审与下一道研究门

这是 2026-10-01 A/B 开发门之后的说明，不改写启动时冻结的协议、
代码和供给证明。副审为只读 Codex，不是外部人类 peer review。
证明技能指定的 gpt-5.5 在当前可用模型中缺失，实际用 inherited Codex；
没有伪称独立特定模型，完整私有交互不入 Git/ZIP。公开摘要在
`integration/checks/{method_review,claim_review}_20261001.json`。

## 证明范围

供给 Propositions 1–4 与固定整数实现通过；Proposition 6 要明确“三个
独立 exact margins、一个整数 lattice coordinate t、M>=0、完整流决定
重建边际及 t'”。它仅是条件熵/preimage cardinality 界，不是文件节省界。
Proposition 5 的全场 refinement 未实现，不进入实验贡献/运行成本。

四角差分是充分证书，不与全部 rectangle 合同等价。DP 精确性仅针对
固定 incoming prefix row，lex(off-lattice count,current-row prefix²)；
tie 是较小的 immediate predecessor/final state，不是已证明的全路径
前向 lex 最小。零 fine 的判据也只在同一固定入边与 prefix ball 内成立。

全场最优反例：H=2,W=1,U=4,B=1,q=4，X=(2,2)^T。初扫复制 X，fine=2；
但 Y=(1,4)^T 合法，prefix=(-1,1)^T，fine=1。行精确不能外推全场精确。

当前 W=512,B<=250,U=10000：单行次目标 <=32,000,000、总场 sum
<=2,621,440,000、state index<=500，int64/int32 安全。不能凭当前
guard 泛化任意数值尺度。复杂度在 unit-cost 整数下 O(HW(2B+1))，
B 是数值预算，故 pseudopolynomial；编码器/全部矩形审计另有成本。

供给 coarse diagnostic 先 cast int64 再验证，非整数 0.9 可被截断为 0。
当前全部调用已在整数域，未影响结果。这个 API caveat 保留记录；未来
公开 API 应另版本严格拒绝非整数输入，**不改本轮绑定原型来伪造原运行**。

## 原创性不能凭通过开发门推断

| Primary predecessor / 阅读范围 | 明确重合 | 本候选尚待核对的差异 |
|---|---|---|
| [Lyu–Wang 2020，相关 §§2.2/2.4](https://arxiv.org/html/2005.08487v1) | bounded 2D state 与 mixed difference / consistent reconstruction 已有 | hard in-box integer alphabet、保护约束、conditional minimum off-lattice 与 interval/residue 加速 |
| [Asano et al. 2003，副审读取相关 §§1–4](https://dspace.jaist.ac.jp/dspace/bitstream/10119/4906/1/B3022.pdf) | matrix rounding、regional discrepancy、特殊 region family 的高效优化已有 | 本候选用充分 prefix ball 与完整细整数选择，不是解决经典所有矩形 binary rounding 的全局最优 |
| [DCC2020 TCQ，副审读取 §3.2](https://arxiv.org/html/2001.09417) | trellis path/minimum-cost traceback 已有 | 本问题的 hard physical/prefix state 与 interval/congruence 结构 |
| [QPET，相关 §§4–5](https://www.vldb.org/pvldb/vol18/p2440-liang.pdf) | QoI 预算调节、验证和付费 outlier correction 已有 | 直接构造满足隐式全部 rectangle 证书的合法场，而非对已配置 region 修正 |
| [TOPIQ 2026，相关方法全文](https://arxiv.org/html/2608.26912v1) | post-hoc spatial QoI prediction 已有；其统计预测不是 deterministic preservation | 本候选的严格 simultaneous 服务不同，不因此拥有 post-hoc 领域首次 |
| [ICML2026 Ugalde–Armour，仅 official abstract](https://proceedings.mlr.press/v306/ugalde26a.html) | physics-aligned compression / geometry 与 entropy-distortion 已有 | full PDF 尚未读取，不据摘要作精确排重/absence 结论 |

相关全文指可访问的相关方法段已读，不是凭 abstract 推断完全等价。
Asano 初次 author PDF 字符抽取失败，副审从上表 JAIST readable copy
读取；root 原轮未读其完整证明。ICML 题目是 **A Geometric Lens on
Physics-Aligned Data Compression**，不是旧 audit 误标的 DiscQuant。

Lyu–Wang 的稳定构造扩展输出 alphabet，但其 greedy stability theorem
**不能证明所有非因果 in-box 量化均不可能**。我们的复制源路径已给出
可行性。零 fine interval 是 elementary chain reachability，有诊断价值，
不单独包装范式创新。搜索未定位完全同一 oracle 仅是 bounded search，
不是已证明原创。今后必须在 exact algorithm object 层面继续排重。

## 晋升决定与下一关（尚未执行）

两副审一致：本轮完整付费数字/合法性支持；升为下一轮主候选；不升为
已认证原创论文。现在没有证据需要 refinement，所以实现与 carrier 固定。

下一阶段必须**另冻结协议，在读取新 pixels 前**固定 geography sampling、
窗口 geometry、源身份/重叠排除、全部 joint contracts、两个步长/coder/
scan/ties、基线映射、missing/密度分组和失败保留规则。当前阶段的协议
禁止新 heldout 获取/编码；本文件不是已经执行的留出报告。

首先明确应用接受：是否仅控制 rectangle 总建成面积，是否也要求像元
局部误差、精确双向零支持、mean/特定用途。当前 zero-preserve 只单向。
100/1000 m² 是研究工程预算，不装作业界公认阈值。不擅自把全图源的
statistics、missing 比例、压缩成绩作为选窗依据之后还叫 untouched。

复用相同算法与 paid carrier，保留 identity/paid source-zero control，
覆盖新的低/高密度与真实 missing（若数据产品确有）。若无法获得天然
missing，报告缺口，人工 mask stress 单独列，不能冒充真实覆盖。
所有判决从独立 decode 开始。不要将多个 epsilon 小块重置 prefix 后
拼接并声称仍是同一全局 epsilon；大场要共享全局状态或另证预算分配。

开发门阈值仅决定继续与否，不是 SOTA 门。留出还需 actual-contract
强 codec 比较和原创性核查，保留所有非法/膨胀/identity 个案。
标准化 integrity audit 未完成，当前数字副审判决是 provisional scoped。
