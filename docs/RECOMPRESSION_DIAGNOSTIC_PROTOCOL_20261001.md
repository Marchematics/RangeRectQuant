# 同步长重复压缩：仅用于排除新的研究假设

上一轮 A/B 通过，强简单控制否决昂贵DP必要性。本阶段不是新方法，
不加refinement、不采像元新源；检验另一个真实流程问题是否值得研究。
[SC2025应用需求报告](https://userweb.cs.txstate.edu/~burtscher/papers/sc25b.pdf)
指出重复有损压缩仍需研究；idempotent压缩并非新问题：
[NeurIPS2023 right-inverse方法](https://proceedings.neurips.cc/paper_files/paper/2023/hash/2a25d9d873e9ae6d242c62e36f89ee3a-Abstract-Conference.html)
已明确讨论。本次不靠术语交集认证原创。

## 只有一个主问题

已经合法的direct-field输出，若作为**新的输入**重复使用同一预算/
步长/量化器，局部单步合法是否仍能维持相对原源的一份全局epsilon？
原codec仅保证对本次输入，不曾保证累计；若失败是流程合同缺口，
不能倒改先前成功或指控原保证有bug。没有修改场/模拟物理迭代，
这只是原样homogeneous recompression，不是全部迁移/迭代工作流。

两个强现成量化器：原冻结row DP（RQ01），suffix-viable greedy
（QF01 algorithm1）。每个各4源×q20/q200，主mode固定lossy。
身份RQ01为8个付费fixed-point控制。zero-preserve不纳入本诊断：
普通API重算source-zero会让保护集合增长，不能把它冒充固定集合实验。
NoData沿原mask保留；四源自然NoData0，不新增真实missing覆盖宣称。

## 固定矩阵与输出

pass1取已审查/hash绑定的8DP+8greedy+8identity原packet/output。
DP/greedy每条链依次实际编码并冷解码pass2至8，不跳过中间代数、不
挑最小码长checkpoint，不把多次epsilon相加称原epsilon。共112新流。
identity各实际重编码pass2（8流）；pass3至8不运行，后续不变由
复制源的定义证明，不计入实际encoder/worker数。最多120新流/worker。

量化器、tie、coder、geo、mask、q/B不变，使用各自原RQ01/QF01格式；
within-chain比较同格式。两算法carrier有小metadata差异，**不据
跨算法字节差给rate排名**。每流全部header/config/mask/checksum与
quotient/remainder收费；存完整packet/body/冷decode/worker/logs。

所有新流从另进程source-free decoded field验证：整数范围、mask、
1024固定direct queries、local prefix、独立local和相对原源的全部
矩形最大误差。保存改变像元、fine、完整码长及quotient/remainder。
source/prefix不传worker；上一步decoded field只作为下一步encoder输入。
允许cumulative失败继续诊断，但局部合法性/decoded一致性失败作为
异常停止该链，并保留partial/失败，不偷偷改参数重跑。

## 预注册判决，不把普通非幂等放大成论文

- 逐链报告第2步与所有后续步是否field-idempotent、首次累计超预算
  和pass2/4/8值。fully coarse合法输入是两图的fixed point：u=0、
  b=0给零fine/零energy且合法，greedy同样选b=0。此为直接证明，不是
  新发明。测试同时验证该性质。
- **进入“严重累计漂移”研究的门**：对每个算法，两个预算分别至少
  3/4源在pass8相对原源超过epsilon，同时该算法全部112/2单步输出
  局部合法。只有该算法两预算均过，才把该冻结配置的严重漂移晋升
  为新方法动机。不是SOTA/原创门；单个反例仅否定普遍保证。
- 如果仅少数tiny变化、累计仍合法或第二次即固定，不开发复杂
  idempotence修补，不以改epoch/q/数据/支持约束挽救假设。只保留
  清楚的scope caveat，换研究问题。fine下降但paid bytes上升同样保留。

CPU单线程，GPU0，120s/worker、整矩阵900s硬上限，估计5CPU分钟，
额外evidence≤200MiB。先synthetic correctness、完整hash冻结并push
clean tree，再加载用于本新诊断的真实fields。不改任何已绑定文件。
失败门保留；不宣布重要原创、留出、应用认可或整体目标完成。
