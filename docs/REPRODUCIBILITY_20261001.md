# 复现与交付范围

独立私有仓库：https://github.com/Marchematics/RangeRectQuant 。未加覆盖
供给材料/数据的许可；再分发或公开前要核对上游权利。没有 token、凭据、
`.venv`、缓存、`.git` 或私有 `.aris` trace 进入交付包。

## 保存什么

- `imports/` 原 ZIP、`supplied/` 43 原文件及内部 hash，逐字节不变。
- `data/` 四真实源和固定 1024 queries，含 Tokyo 同窗容器修复 provenance。
- `evidence/previous/` 48 件付费 native-winner/BF01 packet、body、full decode
  及 worker；参考报告/acquisition/repair 保留。不是完整旧工程的替代。
- `src/` 冻结原型/RQ01；`experiments/` 编码、独立解码、检查与纯保存输出
  分析；`tests/` 安全显式测试；文档/环境/启动前冻结记录。
- `results/pilot_20261001/` 24 实际 paid packets、24 full outputs、body、
  worker/query/logs、ledger/report；`results/replay_20261001/` 另24 fresh
  重解码；非法跨预算记录保留。摘要/事后机制诊断不假装启动前预测。

## 独立解码（不需要原始 LinewiseROI 或优化器）

在仓库/解包根目录创建自己的 Python 环境，固定版本见 requirements 与
`integration/environment.lock.txt`。本轮 Python3.12.14 / macOS arm64，
NumPy2.3.5 / Numba0.65.1 / llvmlite0.47.0。跨 OS 的 RSS 单位及 bitwise
编码不可直接当同一环境结果。不要在 supplied 目录运行会覆盖证据的脚本。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export PYTHONPATH="$PWD/src:$PWD/experiments"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
.venv/bin/python -m unittest tests.test_correctness tests.test_packet -v
mkdir /tmp/rq01-example  # 必须用新目录；不要覆盖保存结果
.venv/bin/python experiments/worker.py \
  results/pilot_20261001/packets/paris-q20-lossy.rq01 \
  /tmp/rq01-example/decoded.npz /tmp/rq01-example/worker.json \
  --queries data/queries.npy
```

worker 只接受 packet 与 queries，不读取 source。一次 full decode 是
自包含科学服务，但不是独立完成全部历史 hash/合同审计的代名词。

## 本地完整历史审计与原环境绑定

`experiments/verify_saved.py` 有意验证启动前绝对 runtime path/hash，并
要求兄弟目录 `../LinewiseROI` 提供原745文件及 manifest。
因此 ZIP **不是无需准备即能重跑原 frozen audit 的 standalone 环境**。
历史上一套本地命令是：

```sh
.venv/bin/python experiments/verify_saved.py \
  --source results/pilot_20261001 --out /tmp/rq01-new-replay
```

换机器必须另建立并明确标注新环境/lineage 验证方案，不能改旧 preflight
后说原83绑定仍然通过。编码 runner 还要求 clean pushed tree、保留原冻结
hash 和新输出目录；无需为查看证据重新启动 codec。新源属于后续阶段。

交付脚本 `integration/package_release.py` 从 clean pushed Git commit 打包
并逐 payload 核对 Git blob、SHA256 和 ZIP CRC；内部 release manifest 记录
准确 source commit。外部 receipt 记录 ZIP SHA/尺寸/检查数，随后独立
提交，避免自引用。包不包含 Git database，可从同一 commit 再 clone。
