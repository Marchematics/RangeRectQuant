"""Deliver current source/data/results and every new complete review file."""
import argparse
import json
from pathlib import Path
import subprocess
import zipfile
from package_release import ROOT,DELIVERY,git,sha
from package_expanded_release import write_bundle


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    out=parser.parse_args().out.resolve()
    if out.exists() or not out.is_relative_to(DELIVERY):raise ValueError('New delivery directory required')
    revision=git('rev-parse','HEAD').decode().strip()
    if git('status','--porcelain') or git('ls-remote','origin','refs/heads/main').decode().split()[0]!=revision:
        raise ValueError('Clean pushed source snapshot required')
    verified=json.loads((ROOT/'integration/checks/review_delivery_validation_20261002.json').read_text())
    final=json.loads((ROOT/'paper/notes/final_validation_20261002.json').read_text())
    if verified['complete_sourcefree_files']!=4232 or final['pages']!=10 or final['pdf_sha256']!=sha(ROOT/'paper/main.pdf'):
        raise ValueError('Verify final results and article first')
    out.mkdir(parents=True);receipts=[]
    common=dict(source_commit=revision,repository='https://github.com/Marchematics/RangeRectQuant',
                gpu_used=False,repository_private=True,existing_complete_study_release='expanded-study-20261002-af0b24f')
    source=out/'RangeRectQuant-Review-Source-Data-Results.zip'
    subprocess.run(['git','-C',str(ROOT),'archive','--format=zip','--prefix=RangeRectQuant/',
                    '--output='+str(source),revision],check=True)
    vendor=[];legacy=ROOT.parent/'LinewiseROI'
    with zipfile.ZipFile(source,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name in ('built_area_packet.py','built_area_discrete_packet.py','built_area_fiber_packet.py',
                     'built_area_integer_metrics.py','built_area_metrics.py','native_sz3_worker.py',
                     'native_mgard_driver.cpp','native_qpet_api_v2_driver.cpp','built_area_acquire.py'):
            p=legacy/'experiments'/name;label='LinewiseROI/experiments/'+name
            archive.write(p,label);vendor.append(dict(path=label,sha256=sha(p)))
        for name in ('native_runtime_20261001.json','qpet_native_api_v2_build_20261001.json'):
            p=legacy/'integration/checks'/name;label='LinewiseROI/integration/checks/'+name
            archive.write(p,label);vendor.append(dict(path=label,sha256=sha(p)))
        archive.writestr('SOURCE_SNAPSHOT.json',json.dumps(dict(common,vendored_dependencies=vendor,
            native_execution='Set matching Python and native driver paths; no environment or binary installation bundled'),indent=2)+'\n')
    with zipfile.ZipFile(source) as archive:
        if archive.testzip() is not None:raise ValueError('Source CRC')
    receipts.append(dict(archive=source.name,bytes=source.stat().st_size,sha256=sha(source),git_archive_source=True))
    paths=sorted(p for name in ('review_revision_20261002','review_dense_20261002') for p in (ROOT/'results'/name).rglob('*.packet'))
    if len(paths)!=4232:raise ValueError('Review packet count')
    receipts.append(write_bundle(out/'RangeRectQuant-Review-Complete-Files.zip',
        [(p,'RangeRectQuant/'+str(p.relative_to(ROOT))) for p in paths],dict(common,complete_review_files=4232)))
    paper_entries=[]
    for name in ('main.tex','references.bib','dccpaper.cls','IEEEbib.bst','README.md','template/PROVENANCE.md'):
        paper_entries.append((ROOT/'paper'/name,'paper/'+name))
    paper_entries.extend((p,'paper/'+str(p.relative_to(ROOT/'paper'))) for p in sorted((ROOT/'paper/sections').glob('*.tex')))
    for name in ('frontier','review_mechanism','mechanism','closest'):
        paper_entries.append((ROOT/f'paper/figures/research/{name}.pdf',f'paper/figures/research/{name}.pdf'))
    receipts.append(write_bundle(out/'RangeRectQuant-DCC-Paper-Source.zip',paper_entries,dict(common,role='Ten-page article, complete compile inputs')))
    pdf=out/'RangeRectQuant-DCC-Paper.pdf';pdf.write_bytes((ROOT/'paper/main.pdf').read_bytes())
    receipt=dict(status='PASS_REVIEW_SNAPSHOT_CRC_AND_SHA',source_commit=revision,archives=receipts,
                 complete_review_files=4232,pdf_sha256=sha(pdf),unit_tests=42,article_pages=10,
                 prior_paid_files_and_original_downloads='Use unchanged expanded-study-20261002-af0b24f assets',
                 repository_private=True,submission_status='Not submitted')
    (out/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (out/'DELIVERY_CN.md').write_text(f'''# RangeRectQuant 审稿意见后完整更新

源码快照：{revision}。论文已填写提供的三位作者、单位和通讯邮箱，共10页。
新增4232个完整解码文件，42项单元测试通过，GPU0。

`RangeRectQuant-Review-Source-Data-Results.zip`含当前全部已提交源码、裁剪数据、
结果与失败记录，及兄弟目录`LinewiseROI/`中的11项原有重现依赖。
`RangeRectQuant-Review-Complete-Files.zip`含本轮全部4232个完整文件和逐项SHA。
两包解压至同一父目录合并。论文源码小包可单独编译。

原研究7066个完整文件、5项额外原生重放及完整产品下载保持原封不动，继续使用：
https://github.com/Marchematics/RangeRectQuant/releases/tag/expanded-study-20261002-af0b24f
本次不重复上传这些历史大文件。新源码包替换旧源码包，其余旧资产可直接沿用。

细像元几何与有限码长、同场编码、步长、层次总量和原生密度五块已完成。
扩大层次参照后512平方、预算1000仍40地点全胜，字节减少41.30%。
详情：`RangeRectQuant/docs/REVIEW_REVISION_RESULTS_20261002.md`。
文章未提交。匹配的原生运行时需要按既有重现文档配置，不包含环境安装包。
''')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
