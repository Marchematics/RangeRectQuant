# 新地理留出：检验直接合法场的可迁移率收益

目的：检验原轻量直接场构造在此前未载入像元的地理窗口中，是否仍
优于同合同强控制。不是要求所有primitive新造；方法定位见
`RESEARCH_POSITION_20261001.md`。冻结后不依据像元/结果换城或移窗。

## 数据与固定方法

新Cairo(31.2357,30.0444)、Delhi(77.2090,28.6139)、New York
(-74.0060,40.7128)、Jakarta(106.8456,-6.2088)。同GHS-BUILT-S
E2020 R2023A、100m原生UInt16；512²窗口按指定中心投影到ESRI:54009、
取floor后的中心像元再减256，不缩放。官方tile grid元数据已用于
定位，像元尚未获取；URL/row/col/expected affine见assets清单。

主方法：原suffix-viable greedy、raster scan/tie/paid QF01不变，
(q,epsilon,B)=(20,100,25)/(200,1000,250)，默认lossy。原RQ01条件行
DP两配置作内部oracle/control；不是用开发源选新步长。付费mask与
共同SUM/count endpoint不变，valid零允许变化。

每源外部控制沿用既有38项BA02固定grid：6无损整数表示、lossless
JPEG2000、15 SZ3、8MGARD、8QPET；三BF01模式0/25/250。共每源
45实际流（38+3+2DP+2greedy），四源180，两个预算分别判决。基线
取该源该预算最小合法外部流，是有利于基线的固定pool oracle；不从
heldout选择主方法参数。所有失败/非法/原生异常保留。

## 判断

八个主服务必须非平凡、整数范围/mask合法、全部矩形误差≤对应预算，
source-free full decode/1024 direct queries正确。两预算各自要求
至少3/4严格胜出、aggregate≥10%付费减少、无源>5%膨胀；未过就
报告未过，不改门。费用包括body/header/config/mask/geo/checksum。
DP额外率/细位置/计算量另表，不恢复“昂贵DP必要性”命题。

先保存未编码source SHA/geo/source统计，再绑定实验代码、控制源码/
runtime、原方案/hash和数据，clean push后实际编码。跨tile/全图保证
不由此推出；这是一份512²场的全矩形合同。直接query samples只验证
接口，全部矩形结论必须来自完整几何计算。冷时延/RSS只作单次实测
记账，不据此宣布统计性能支配。

## 获取及运行界限

本机CPU单线程，GPU0；项目数据/缓存/结果各独立。沿用已有隔离
GHSL acquisition runtime和native control runtime，不修改作者数值库。
每archive≤256MiB，下载timeout180s；每worker120s、矩阵1800s。
未完成/获取错误保留manifest，不根据有利像元替换窗口。归档zip留
本项目ignored `.acquisition/`，source crops、来源/HTTP/CRC/hash在Git。

这是新**地理**留出，不是产品跨域或应用阈值已经认可；仍可以检验
方法效果。missing/density压力实验另固定设计，并行补证，不阻塞本门。
