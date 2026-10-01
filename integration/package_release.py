"""Package a clean pushed scientific snapshot; verify every payload blob."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT.parent / 'deliverables'


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
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
        raise SystemExit('Need the exact snapshot pushed to origin/main')
    names = [n.decode() for n in git('ls-files', '-z').split(b'\0') if n]
    if not names:
        raise ValueError('Empty snapshot')
    entries = []
    for name in sorted(names):
        path = Path(name)
        if (path.is_absolute() or '..' in path.parts or
                any(p in ('.git', '.venv', '.aris', '__pycache__') for p in path.parts) or
                path.name.startswith('.env') or path.suffix in ('.pyc', '.nbc', '.nbi') or
                (ROOT/path).is_symlink()):
            raise ValueError('Private/runtime/unsafe payload: '+name)
        raw = (ROOT/path).read_bytes()
        if raw != git('show', revision+':'+name):
            raise ValueError('Payload differs from Git snapshot: '+name)
        entries.append(dict(path='RangeRectQuant/'+name, bytes=len(raw),
                            sha256=hashlib.sha256(raw).hexdigest()))
    manifest = dict(
        format='RANGERECTQUANT_SCIENTIFIC_SNAPSHOT_1', source_commit=revision,
        source_repository='https://github.com/Marchematics/RangeRectQuant',
        launch_commit='db30535f47a63cd5c137a68c84488d2e15c70ba3',
        payload_files=len(entries), entries=entries,
        sourcefree_decoder_self_contained=True, full_historical_audit_standalone=False,
        historical_audit_requires='../LinewiseROI original 745 files/manifest and original absolute runtime bindings',
        environment_included=False, development_sources_only=True,
        novelty_established=False, sota_established=False,
        created_local=datetime.now().astimezone().isoformat())
    delivery = f'''# RangeRectQuant 方法/实验/数据整合快照

科学 snapshot `{revision}`；实际编码启动 `{manifest['launch_commit']}`。
四已观察开发窗、两个固定工程预算；八预定服务非平凡合法，完整费用
较更强 prior（含 BF01）减少30.79%/56.14%。不是heldout/SOTA或原创认证。

解压得到独立 `RangeRectQuant/`：原43文件/原ZIP、active code/tests/协议、
四源NPZ/查询、48prior artifacts、24paid packet/full decode/worker、
24fresh replay及失败/logs、两只读AI副审摘要、结果CSV/完整收费分解。
无需旧增量包即可独立解码RQ01；不读取source/prefix state/固定边际。

**完整历史审计不是即开即跑**：verify_saved.py 要求兄弟LinewiseROI原745
文件及启动前绝对runtime path/hash。换机器需明确建立新环境/lineage验证，
不可改旧preflight后冒称同83绑定。没有带入旧工程全部native archives。
具体入口/版本与区别见 `RangeRectQuant/docs/REPRODUCIBILITY_20261001.md`。

没有runtime/.venv/.git/私有AItrace/凭据；不上GPU。原745与20历史JPEG
失败未改。供给材料/数据rights未被重新授权；repo保持private。SHA/CRC/
Git blob通过只证明交付一致，不证明原创性、科学审计完成或SOTA。
下一关是另冻结未观察地理源与用途合同，不为增加章节再加refinement。
'''
    out.mkdir(parents=True)
    archive = out/'RangeRectQuant-Code-Data-Results-20261001.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for row in entries:
            bundle.write(ROOT/row['path'].removeprefix('RangeRectQuant/'), row['path'])
        bundle.writestr('PACKAGE_MANIFEST.json', json.dumps(manifest, indent=2)+'\n')
        bundle.writestr('DELIVERY_CN.md', delivery)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None or len(bundle.infolist()) != len(entries)+2:
            raise ValueError('ZIP CRC/entry count')
        for row in entries:
            raw = bundle.read(row['path'])
            if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('ZIP payload SHA: '+row['path'])
    receipt = dict(
        status='PASS_RANGERECTQUANT_CRC_SHA_GIT_BLOB', archive=str(archive),
        archive_bytes=archive.stat().st_size, archive_sha256=sha(archive),
        source_commit=revision, payload_files_verified=len(entries),
        total_zip_entries=len(entries)+2, payload_bytes=sum(r['bytes'] for r in entries),
        supplied_files_preserved=43, historical_files_preserved=745,
        sourcefree_decoder_self_contained=True, full_historical_audit_standalone=False,
        private_review_traces_included=False, novelty_established=False, sota_established=False)
    for filename, value in (('PACKAGE_MANIFEST.json', manifest), ('PACKAGE_VERIFICATION.json', receipt)):
        (out/filename).write_text(json.dumps(value, indent=2)+'\n')
    (out/'DELIVERY_CN.md').write_text(delivery)
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == '__main__':
    main()
