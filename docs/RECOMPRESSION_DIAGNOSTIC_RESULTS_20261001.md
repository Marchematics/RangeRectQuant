# 重复保存的流程边界：局部合法，原源合同不自动继承

固定协议一次完成120个新paid packet/冷source-free full decode，零异常，
CPU约143秒、GPU0。112个主链步骤均相对本次输入合法，却全部超过
相对原源的预算；16条链都从pass2开始超出。八个identity控制在实际
运行的pass2中field/body/完整packet不变，pass3–8没有运行。

这不推翻原单次压缩收益，也不是原codec保证有bug。原codec只保证
对本次输入的误差；每次重置预算并不能免费继承一份原源epsilon。

## 结果与率代价

|算法/预算|pass1完整B|pass8完整B|额外节省|最终最大误差/预算范围|
|---|---:|---:|---:|---:|
|DP/100|787191|785467|0.2190%|1.060–1.390|
|DP/1000|470287|468243|0.4346%|1.049–1.311|
|greedy/100|791384|786636|0.6000%|1.610–2.390|
|greedy/1000|474256|468800|1.1504%|1.231–1.840|

各算法两预算的预注册动机门都通过：pass8均4/4源超预算，全部局部
转移合法。但这是**有界、随后稳定的超预算**，不是无限持续漂移。
DP在pass2–3变成全粗场，pass3–4起重复field/packet一致；greedy相应
为pass2–5和pass3–6，之后实际检查至pass8均一致。

全粗场是两个映射的fixed point：零prefix路径复制粗场，fine与状态
能量都为零，greedy亦选零状态。这解释这些观察，不证明任意输入
都在相同轮数收敛。São Paulo greedy/q200的pass2→3，fine31→0而完整
码长121767→121839B，反向变化保留，没有挑选最小checkpoint。

## 对研究主线的含义

固定quotient/config/mask不变，即使令greedy的整个remainder免费，
两个原控制流也最多省0.8355%/1.5241%（DP0.3578%/0.6465%）。因此不
继续为fine-count-only优化投入复杂模块；这个账单界不限制改变商、
格点步长或表示的办法。更重要的开发收益仍是原直接场构造本身。

[SC2025应用需求报告](https://userweb.cs.txstate.edu/~burtscher/papers/sc25b.pdf)
把迭代压缩列作需求；root已读相关takeaway。另一方面，
[NeurIPS2023 right-inverse工作](https://proceedings.neurips.cc/paper_files/paper/2023/hash/2a25d9d873e9ae6d242c62e36f89ee3a-Abstract-Conference.html)
明确研究幂等压缩（本轮official abstract，不冒充完整算法精读）。
该诊断作为使用边界/消融，不另包装一篇“发现非幂等”的方法论文。
按用户最新定位，继续联合合同的轻量主方法和新地理验证。

## 可复现证据

启动clean pushed `f0c884e83871dfc8ef6ce4f140620349358ed7bb`；协议与
量化器未改。`results/recompression_20261001/`保存launch/ledger/report、
120个packet/body/decoded field/worker、fees及全部失败判决；
`attribution.json`、`cases.csv`、`chains.csv`给出率/lineage/稳定性。

只读独立副审核对480新artifact SHA、120链输入、120新+24旧packet、
122880 direct queries与240新+24初始all-rectangle值，完整report复算
相同；83/157/228重叠binding集合及43/745/48原件PASS。其几何实现
未导入runner的算法。根执行者另做saved-data归因，未新增encode或
worker，不把重复读取算新实验。

18明确选定安全测试通过；自然NoData0、四已观察源、工程预算沿用。
本诊断无需被叫作重要原创，才能为一项扎实研究提供有效边界证据。
