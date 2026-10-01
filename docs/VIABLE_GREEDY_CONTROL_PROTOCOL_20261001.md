# 下一道必要性门：排除 O(HW) viable-greedy 解释

这是 A/B 成功后的**强机制控制**，不是修改主候选，不采新源，不叫留出。
成功的原 DP/RQ01 与供给文件保持 frozen。此前单纯 myopic greedy 可能
死路，不代表所有轻量 greedy 均失败；不拿弱贪心撑新方法必要性。

## 普通 interval viability 已足够保证完整物理可行

固定入边 u，t_j=x_j-(u_j-u_(j-1))，y_j=t_j+b-a。
令列 j 之后完整整数后缀可行状态为 [L_j,H_j]，终点 [-B,B]。
未保护位置的 backward predecessor interval 是
`[-B,B] intersect [L_j+t_j-U,H_j+t_j]`。
保护 y=x 时 b=a+delta，predecessor interval 是
`[-B,B] intersect [L_j-delta,H_j-delta]`。
完整整数输出/单调区间归纳给出 exact suffix viability；源复制路径保证
初始0在可行区间。这里不声称这些基础 interval 操作原创。

Forward 时在 legal range 与 suffix corridor 交集中优先选
`b == a-t (mod q)` 的粗化状态，取 b² 最小/lower b tie；无粗解则取
任意合法整数中 b² 最小/lower b tie。保护位置固定。可行性由 suffix
viability 归纳保证，每列 O(1)，每行 O(W) 内存、全场 O(HW) 时间，
unit-cost 整数假设。它**不保证整行 fine count 最优**，但可能已经足够
解释原码长成绩，是必须排除的更强简单控制。

## 本轮一次性矩阵

固定原四开发窗、q20/q200、lossy/zero-preserve、raster rows/min b²/lower
b tie、原 u16 shuffle/LZMA6；16次greedy场构造，不调新参数。
从原 RQ01 保存且hash绑定的16 DP非identity场重编码，不复跑 DP。
共32 QF01 paid packet / 32新source-free full worker，两预算64 verdict。
QF01两算法共享完全相同解码器/fee字段，algorithm_id=0/1实际付费。
分别报告 body和metadata差异；核对重编码DP body等于原RQ01 body。
新carrier不改变场、合同或coder；不能用免费数组payload比较完整码流。

从冷解码场独立prefix/range/mask/源零保护/allrectangle/1024direct slice
验证。另在 DP固定incoming row上检查 greedy fine >= 原 conditional
minimum；全场u不同，不伪称全场DP必然支配greedy。

仅两主张：轻量控制是否联合可行且实际同样小；精确row DP的额外费用
收益是否足以支撑必要性。预先将**DP必要性研究门**固定为两个预算各
≥3/4 strict paid wins、四源总bytes比greedy再少≥10%、单源膨胀≤5%、
全部非平凡合法。zero-preserve单独消融，不挑mode。这不是用户先前B
门，也不是SOTA标准。若不过，不倒改先前30.79%/56.14%的真实结果，
但撤回“复杂DP是这些率收益所必需”的设想；查新/稿件中心需另证。

代码/协议/测试/queries/源和原DP输出先hash绑定并push clean tree。
CPU单线程/GPU0，每worker120s，整体1800s。正确性测1,000随机row与
DP下界、1,000独立穷举greedy选择、250full field、小packet收费/篡改；
不覆盖原测试/包/结果。不启动native codec或 heldout acquisition。
