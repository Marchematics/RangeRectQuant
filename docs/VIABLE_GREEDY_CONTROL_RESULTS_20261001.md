# 强简单控制：DP 必要性门失败，直接合法场的收益仍成立

**结论：本轮否决“昂贵的精确 row DP 是当前显著压缩收益所必需”这一
解释，不否决原 A/B 的完整收费成绩。** 原主方法、43供给文件、745历史
文件和原结果不动；这个 O(HW) 控制不是另一个已认证原创方法。

预注册入口 `docs/VIABLE_GREEDY_CONTROL_PROTOCOL_20261001.md`，clean/pushed
启动 `2cc62e6ceba9331aa5eba56e030704632f47ad00`，UTC 11:14:49。
四个已观察开发窗，q20/q200、原工程预算100/1000、lossy/zero-preserve，
扫描/最近零状态/lower-state tie、UInt16 shuffle+LZMA6均预先固定。
未采新源、未改原 DP、未加 refinement，CPU/GPU0。

## 为什么这是更强而公平的控制

先 backward 算**完整整数输出的后缀可行区间**，再 forward 尽可能选粗
格点。源复制路径保证初态可行；每个 forward 选择留在后缀可行区间，
因而不会像供给的 myopic greedy 那样走入死路。保护位置强制复制源。
每列常数次整数区间/余数运算，全场 O(HW)、行工作空间 O(W)，不保证
fine count 最优。这是经典 viability 技巧，不能改名当范式创新。

16次新 greedy 全场构造；另外16个原保存、hash绑定的 DP 场**只重编码**，
不重跑 DP 优化器。两算法均进入同一 QF01 paid carrier，algorithm_id
也实际收费。16 DP body 与原 RQ01 body 逐字节相同、decoded fields 相同。
QF metadata略短，故下面的 DP 总数与原 RQ01略不同；不能倒改原表。

## 完整 paid bytes：两道 ≥10% 额外收益门均 FAIL

| epsilon | QF01 saved DP | QF01 viable greedy | DP额外减少 | DP / greedy fine |
|---:|---:|---:|---:|---:|
|100|787,137|791,384|**0.53665477%**|426 / 1,595|
|1000|470,236|474,256|**0.84764347%**|482 / 1,618|

每预算 DP 都4/4严格更小、无源膨胀、全部非平凡合法，但预注册的总收费
额外减少≥10%没有满足。zero-preserve同样只有0.33430042%/0.52153003%
额外减少（830,298 vs833,083；514,626 vs517,324）。不挑 mode 救门。

|site|DP q20|greedy q20|DP q200|greedy q200|
|---|---:|---:|---:|---:|
|Paris|182,631|184,143|112,718|114,454|
|Tokyo|241,579|242,122|143,765|143,965|
|Lagos|153,987|154,947|91,650|92,710|
|Sao Paulo|208,940|210,172|122,103|123,127|

这个控制仍较已命名 stronger prior（含BF01）减少30.4228%/55.7734%。
原 RQ01 的30.7914%/56.1436%真实成绩与 A/B 成功**不变**，但其中几乎
全部可由轻量构造实现。四窗不是留出，所列prior不是完整SOTA覆盖。

## fine 不是主要码长瓶颈

DP 的 fine 减少73.29%/70.21%，但 quotient 流占主要费用。q20 时 DP
只少452 quotient B、3,796 remainder B，config还少1B；q200 时 DP
少4,188 remainder B，而 greedy 的 quotient **反而少168B**。
因此“更少 fine ⇒重要额外率收益”在当前冻结数据上没有成立。
`results/viable_greedy_20261001/{cases.csv,attribution.json}` 保存32例的
完整收费分解；归因是事后解释，不冒充新的预测实验或字节最优证明。

## 验证与明确限制

- 32新source-free worker完整解码；两预算64判决 **48LEGAL/16ILLEGAL**，
  异常0。16非法均为q200在更紧epsilon100下，完整保留。32指定预算
  服务全部非平凡合法。全矩形独立算法与32,768 direct slices一致。
- 15明确选定测试通过；包括1,000随机row vs DP下界、1,000独立穷举
  greedy选择、250全场、packet/冷worker与原10项。不是discover-all。
- 只读副审独立解析32流、128artifact SHA、157新/83原frozen bindings、
  43/745/48保留项，通过；16保存DP流和原流的body/field一致。
  8,192 same-incoming row只核对保存计数不低于DP minimum，**不是
  新优化器运行，也不是全场DP必然支配greedy定理**。
- root另用只读std-library归因脚本核对上述SHA/收费/原DP body，不重复
  全矩形算法。没有标准化EXPERIMENT_AUDIT或human review，判决provisional。
- 全矩阵24.44298秒含编码/解码/审计；单次greedy构造0.0136–0.0164秒
  不能与未重跑的DP构造比较，不声称实测speedup/峰值内存优势。
- zero-preserve仅 X=0⇒Y=0；没有正支持不变、用途认可预算或真实missing
  覆盖。原JPEG20失败没有修复。无新稿、原创性/留出/SOTA完成声明。

## 当前路线决定

保留直接合法场与原DP作为可信候选/对照；停止把 DP exactness 或加速
当作重要原创贡献的主支柱，也不为扩大方法而加 entropy DP/refinement。
先找出**这个强简单控制无法解决的、实际收费重要的科学问题**，明确
非经典差异和可证伪预测，再另冻结未观察源/应用合同/强codec/重复成本
实验。如果没有重要剩余差距，转向，而非重命名greedy、刷toy或降目标。

本页更新当前决定；原 `REVIEW_AND_NEXT_GATE_20261001.md` 的“下一关先
留出”保留为A/B之后、强控制之前的历史判断，不再作为当前唯一下一步。
