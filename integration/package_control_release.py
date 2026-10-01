"""New full snapshot including the failed DP-necessity control; no overwrite."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import zipfile

from package_release import ROOT, DELIVERY, git, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    out = parser.parse_args().out.resolve()
    if out.exists() or not out.is_relative_to(DELIVERY):
        raise SystemExit('Need a new directory within deliverables')
    if git('status', '--porcelain'):
        raise SystemExit('Need a clean committed scientific snapshot')
    revision = git('rev-parse', 'HEAD').decode().strip()
    remote = git('ls-remote', 'origin', 'refs/heads/main').decode().split()
    if not remote or remote[0] != revision:
        raise SystemExit('Need this exact snapshot pushed')
    names = [n.decode() for n in git('ls-files', '-z').split(b'\0') if n]
    if not names:
        raise ValueError('Empty snapshot')
    entries = []
    for name in sorted(names):
        path = Path(name)
        if (path.is_absolute() or '..' in path.parts or
                any(p in ('.git', '.venv', '.aris', '__pycache__') for p in path.parts) or
                path.name.startswith('.env') or path.suffix in ('.pyc', '.nbc', '.nbi') or
                (ROOT / path).is_symlink()):
            raise ValueError('Private/runtime/unsafe payload: ' + name)
        raw = (ROOT / path).read_bytes()
        if raw != git('show', revision + ':' + name):
            raise ValueError('Payload differs from scientific Git blob: ' + name)
        entries.append(dict(path='RangeRectQuant/' + name, bytes=len(raw),
                            sha256=hashlib.sha256(raw).hexdigest()))
    manifest = dict(format='RANGERECTQUANT_SCIENTIFIC_SNAPSHOT_2', source_commit=revision,
        source_repository='https://github.com/Marchematics/RangeRectQuant',
        original_ab_launch_commit='db30535f47a63cd5c137a68c84488d2e15c70ba3',
        viable_greedy_launch_commit='2cc62e6ceba9331aa5eba56e030704632f47ad00',
        payload_files=len(entries), entries=entries,
        original_ab_pass=True, dp_necessity_gates_passed=[False, False],
        paid_packets=dict(RQ01=24, QF01=32),
        sourcefree_decoders_self_contained=True, full_historical_audit_standalone=False,
        historical_audit_requires='../LinewiseROI original 745 files and absolute frozen runtimes',
        development_sources_only=True, environment_included=False,
        novelty_established=False, sota_established=False, full_goal_completed=False,
        created_local=datetime.now().astimezone().isoformat())
    delivery = f'''# RangeRectQuant 更新整合包：成功与否决都保留

科学snapshot `{revision}`。原A/B启动 `{manifest['original_ab_launch_commit']}`；
强简单控制启动 `{manifest['viable_greedy_launch_commit']}`。不覆盖前一ZIP。

原RQ01开发成绩较所列stronger prior少30.79%/56.14%，继续有效。
新O(HW) viable greedy已能实现30.42%/55.77%；同QF01 carrier的DP
额外只少0.54%/0.85%，两个>=10%必要性门FAIL。不是算法bug，也不能
把重要创新目标降成重命名greedy。当前判断见新结果/查新文档及findings。

独立RangeRectQuant目录含原43文件/ZIP、四源/查询、原24RQ01和32QF01
付费码流、全部full decoded fields/workers/账单/失败/logs、原24fresh
replay、冻结协议/代码/15安全测试、经典文献访问范围与公开副审摘要。
32新流/64预算判决48LEGAL16ILLEGAL0exceptions；指定预算全合法非平凡。
没有heldout、新稿、SOTA或原创认证；没有新真实missing或预算应用认可。

RQ01/QF01 source-free解码不依赖源、prefix state或旧边际；独立目录可
用新环境复放。全历史hash审计仍需兄弟LinewiseROI原745文件和原绝对
runtime绑定，**不是完整即开即跑**。原20JPEG失败未修复、未删除。
包内环境不含.venv/.git/.aris/缓存/凭据。CPU/GPU0，repo仍private；
没有为第三方代码或数据重新授权。SHA/CRC/Git blob校验不认证科学贡献。

旧docs与收据仍作为对应历史快照保留；当前决定由
RangeRectQuant/docs/VIABLE_GREEDY_CONTROL_RESULTS_20261001.md和
RangeRectQuant/docs/EXACT_OBJECT_NOVELTY_20261001.md说明。
复放入口：integration/verify_control_delivery.py；只复放56个保存流，
不调用优化器，不把已观察四窗称留出。
'''
    out.mkdir(parents=True)
    archive = out / 'RangeRectQuant-Code-Data-Results-With-Control-20261001.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for row in entries:
            bundle.write(ROOT / row['path'].removeprefix('RangeRectQuant/'), row['path'])
        bundle.writestr('PACKAGE_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
        bundle.writestr('DELIVERY_CN.md', delivery)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None or len(bundle.infolist()) != len(entries) + 2:
            raise ValueError('ZIP CRC/entry count')
        for row in entries:
            raw = bundle.read(row['path'])
            if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('ZIP payload SHA: ' + row['path'])
    receipt = dict(status='PASS_CONTROL_SNAPSHOT_CRC_SHA_GIT_BLOB', archive=str(archive),
        archive_bytes=archive.stat().st_size, archive_sha256=sha(archive),
        source_commit=revision, payload_files_verified=len(entries),
        total_zip_entries=len(entries) + 2, payload_bytes=sum(r['bytes'] for r in entries),
        paid_packets=manifest['paid_packets'], private_review_traces_included=False,
        full_historical_audit_standalone=False, original_ab_pass=True,
        dp_necessity_gates_passed=[False, False], novelty_established=False, sota_established=False)
    for filename, value in (('PACKAGE_MANIFEST.json', manifest), ('PACKAGE_VERIFICATION.json', receipt)):
        (out / filename).write_text(json.dumps(value, indent=2) + '\n')
    (out / 'DELIVERY_CN.md').write_text(delivery)
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == '__main__':
    main()
