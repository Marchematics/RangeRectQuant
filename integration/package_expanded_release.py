"""Package a committed expanded study and all paid files without overwriting."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from package_release import ROOT, DELIVERY, git, sha


def write_bundle(target, entries, metadata):
    manifest=[]
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for path, name in entries:
            manifest.append(dict(path=name,bytes=path.stat().st_size,sha256=sha(path)))
            archive.write(path,name)
        archive.writestr('PACKAGE_MANIFEST.json',json.dumps(dict(metadata,entries=manifest),indent=2)+'\n')
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None: raise ValueError('ZIP CRC: '+str(target))
        for entry in manifest:
            digest=hashlib.sha256()
            with archive.open(entry['path']) as stream:
                for block in iter(lambda:stream.read(1<<20),b''): digest.update(block)
            if digest.hexdigest()!=entry['sha256']: raise ValueError('ZIP SHA: '+entry['path'])
    return dict(archive=target.name,bytes=target.stat().st_size,sha256=sha(target),files=len(manifest))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    out=parser.parse_args().out.resolve()
    if out.exists() or not out.is_relative_to(DELIVERY): raise ValueError('New deliverables directory required')
    revision=git('rev-parse','HEAD').decode().strip()
    remote=git('ls-remote','origin','refs/heads/main').decode().split()
    if git('status','--porcelain') or not remote or remote[0]!=revision:
        raise ValueError('Clean pushed source snapshot required')
    verified=json.loads((ROOT/'integration/checks/expanded_delivery_validation_20261002.json').read_text())
    if verified['status']!='PASS_SAVED_FILES_AND_FIXED_INPUTS': raise ValueError('Verify complete files first')
    runtime=json.loads((ROOT/'results/runtime_scaling_20261002/report.json').read_text())
    if runtime['status']!='COMPLETE_ATTEMPTED_SCALING': raise ValueError('Scaling unfinished')
    out.mkdir(parents=True); receipts=[]
    common=dict(source_commit=revision,repository='https://github.com/Marchematics/RangeRectQuant',
                gpu_used=False,source_free_files=True,original_inputs_preserved=True)
    # git archive selects exactly committed bytes, including all data/results/methods.
    source=out/'RangeRectQuant-Source-Data-Results.zip'
    subprocess.run(['git','-C',str(ROOT),'archive','--format=zip','--prefix=RangeRectQuant/',
                    '--output='+str(source),revision],check=True)
    legacy=ROOT.parent/'LinewiseROI'
    dependency_names=['built_area_packet.py','built_area_discrete_packet.py','built_area_fiber_packet.py',
                      'built_area_integer_metrics.py','built_area_metrics.py','native_sz3_worker.py',
                      'native_mgard_driver.cpp','native_qpet_api_v2_driver.cpp']
    vendor=[]
    with zipfile.ZipFile(source,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name in dependency_names:
            path=legacy/'experiments'/name; label='LinewiseROI/experiments/'+name
            archive.write(path,label);vendor.append(dict(path=label,sha256=sha(path)))
        for name in ('native_runtime_20261001.json','qpet_native_api_v2_build_20261001.json'):
            path=legacy/'integration/checks'/name;label='LinewiseROI/integration/checks/'+name
            archive.write(path,label);vendor.append(dict(path=label,sha256=sha(path)))
        archive.writestr('SOURCE_SNAPSHOT.json',json.dumps(dict(common,vendored_dependencies=vendor,
            legacy_source_commit=subprocess.check_output(['git','-C',str(legacy),'rev-parse','HEAD'],text=True).strip(),
            native_execution='Use your Python/native driver paths as documented; no virtual environment included'),indent=2)+'\n')
    with zipfile.ZipFile(source) as archive:
        if archive.testzip() is not None:raise ValueError('Source ZIP CRC')
    receipts.append(dict(archive=source.name,bytes=source.stat().st_size,sha256=sha(source),git_archive_source=True))
    packet_root=ROOT/'.aris/evidence/expanded_20261002'
    for size in (256,512,1024):
        paths=sorted(p for p in (packet_root/'frontier').glob(f'*-{size}/*.packet'))
        metadata=dict(common,study='forty geographic locations',size=size,
                      expected_attempts=2200,delivered_files=len(paths),failed_cells_preserved_in_source_results=True)
        expected=2178 if size==256 else 2200
        if len(paths)!=expected:raise ValueError('Frontier packet count: '+str(size))
        entries=[(p,'RangeRectQuant/'+str(p.relative_to(ROOT))) for p in paths]
        receipts.append(write_bundle(out/f'RangeRectQuant-Paid-Files-{size}.zip',entries,metadata))
    paths=sorted(p for group in ('closest','protected','water') for p in (packet_root/group).rglob('*.packet'))
    if len(paths)!=488:raise ValueError('Stress/water packet count')
    receipts.append(write_bundle(out/'RangeRectQuant-Stress-and-Water-Files.zip',
                    [(p,'RangeRectQuant/'+str(p.relative_to(ROOT))) for p in paths],dict(common,delivered_files=488)))
    acquisitions=sorted(p for directory in ('expanded_20261002','water_20261002')
                        for p in (ROOT/'.acquisition'/directory).rglob('*') if p.is_file())
    receipts.append(write_bundle(out/'RangeRectQuant-Original-Product-Downloads.zip',
                    [(p,'RangeRectQuant/'+str(p.relative_to(ROOT))) for p in acquisitions],
                    dict(common,role='Complete official downloads and acquisition headers; cropped sources also in source ZIP')))
    pdf=out/'RangeRectQuant-DCC-Paper.pdf';pdf.write_bytes((ROOT/'paper/main.pdf').read_bytes())
    receipt=dict(status='PASS_EXPANDED_SNAPSHOT_CRC_AND_SHA',source_commit=revision,archives=receipts,
                 packet_counts=verified['groups'],runtime_measured=runtime['measured'],
                 runtime_timeouts=runtime['timeouts'],pdf_sha256=sha(pdf),repository_private=True)
    (out/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (out/'DELIVERY_CN.md').write_text(f'''# RangeRectQuant 完整研究交付

源码快照：`{revision}`。先阅读 `RangeRectQuant-DCC-Paper.pdf`。
六个 ZIP 解压到同一个父目录，合并同名目录；源码、原始产品、完整收费文件
均归入 `RangeRectQuant/`，小型历史依赖归入兄弟 `LinewiseROI/`。
源码包已经包含裁剪数据、方法、结果、失败记录、图表代码和五个额外原生重放文件。
三个尺寸包和压力/水体包另含 7066 个原始完整文件；产品包保存完整官方下载。

40 个新地点 × 3 个尺寸 × 8 个预算均领先预设外部比较池，聚合字节减少
16.23%–72.17%。第二数量保留紧预算负结果；不把比较池领先写成全领域 SOTA。
36 项单元测试通过，全文 10 页。作者姓名和单位仍需填写。
解码、原生运行依赖和历史绑定区别见源码中的
`docs/EXPANDED_REPRODUCIBILITY_20261002.md`。没有打包虚拟环境或凭据。
所有 ZIP 已逐项检查 CRC；完整文件和产品包逐项检查 SHA-256。
顶层 `RECEIPT.json` 记录 ZIP 大小、SHA-256、快照和实验计数。仓库保持私有。
''')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
