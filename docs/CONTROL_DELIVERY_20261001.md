# 强简单控制更新包与验证收据

独立科学snapshot `f63a17752d34a720960c3310e03654524994c674` 已推送
私有 [RangeRectQuant](https://github.com/Marchematics/RangeRectQuant)。
原A/B启动 `db30535f47a63cd5c137a68c84488d2e15c70ba3`；新控制启动
`2cc62e6ceba9331aa5eba56e030704632f47ad00`。原LinewiseROI转移指针
追加提交 `6db0fbc3ea9225bd73ee6886920ac84805cc2c69`，745原件不变。

新完整包（不是overlay，原包不覆盖）：
`/Users/nathmath/dcc/deliverables/DCC_RangeRectQuant_With_Control_20261001_Updated/RangeRectQuant-Code-Data-Results-With-Control-20261001.zip`

- 70,063,112 B；674 payload文件 / 676 ZIP entries。
- SHA256 `e22f9124736993a5381cb71f8bc45962a5af36f22c61b743f608fb560d3edf86`。
- CRC、674 SHA与全部payload对scientific snapshot Git blob一致性PASS。
- 全新临时解包路径 **56 fresh source-free full decodes / 57,344 direct
  queries PASS**：24原RQ01+32新QF01，所有decoded数组与已独立审核场
  相同。使用原runtime，不是新OS/机器，不再重复全矩形算法。
- 本页/新receipt是打包之后提交，不在该固定ZIP中，避免self-reference。
  receipts见 `integration/checks/control_package_*_20261001.*`，完整外部
  manifests/日志也留在交付目录。

包内含43新供给文件/原ZIP、方法/协议/两算法/解码器、四源/查询、
48旧prior artifacts、全部56paid包/body/保存field/workers/费用/失败/
logs，原24fresh replay、32例CSV/费用归因、15安全测试、查新访问范围
与公开副审摘要。没有runtime/.git/.aris/缓存/凭据；仍CPU/GPU0/private。
原数据/第三方代码再分发权利没有被重新授权。

**完整历史审计不standalone**，仍需兄弟LinewiseROI原745文件与原绝对
runtime/hash；新环境可复放source-free服务，但不是原绑定完整复现。
原20JPEG失败与自然missing0保留。旧ZIP SHA也再次核对不变：
`ea156bfbc4071d9db336f9db8905787b017cc9fe2b0b58a2ea19ec27bea830ce`。

执行入口（从解压目录、先建立numpy/numba环境）：

```sh
PYTHONPATH=.:src:experiments python -m unittest \
  tests.test_viable_greedy tests.test_correctness tests.test_packet -v
python integration/verify_control_delivery.py \
  --archive /absolute/path/to/RangeRectQuant-Code-Data-Results-With-Control-20261001.zip \
  --out /new/absolute/path/decode-receipt.json
```

验证器仅运行decoder/query workers，不运行优化器或新源获取；output
已存在会拒绝覆盖。新packager/验证器随scientific snapshot入包。

原开发A/B成功30.79%/56.14%仍有效；新的精确DP必要性两个门FAIL
（额外0.54%/0.85%），轻量control保留几乎全部收益。收费/代码校验
通过不证明重要原创、留出/SOTA或全目标完成，研究目标继续开放。
