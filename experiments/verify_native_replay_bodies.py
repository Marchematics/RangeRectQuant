"""Audit saved bodies that appeared on replay, retaining the original failures."""
import hashlib
import json
import os
from pathlib import Path
import traceback
import zlib

import numpy as np
from research_common import ROOT, ColdDecoder, audit, legal, save, environment, sha
from run_expanded_research import center, crop_geo, BUDGETS
from built_area_discrete_packet import body_codec, roundback, HEADER, EPSILONS, POSTPROCESSOR, digest


def run():
    os.environ.update(environment())
    target=ROOT/'results/native_replay_verification_20261002'
    if target.exists():raise ValueError('Fresh replay verification directory required')
    target.mkdir(); rows=[]; endpoint=ColdDecoder(target/'decoder')
    manifest=json.loads((ROOT/'data/expanded_20261002/manifest_v2.json').read_text())
    frontier=json.loads((ROOT/'results/expanded_frontier_20261002/report.json').read_text())['frontier']
    previous=ROOT/'results/native_failure_replays_20261002'
    try:
        for replay in json.loads((previous/'report.json').read_text())['rows']:
            if replay['status']!='REPLAY_SUCCEEDED':continue
            stem=replay['id']; site=stem.rsplit('-256-',1)[0]; cfg=replay['configuration']
            source=next(s for r in manifest['rows'] if r['site']==site for s in r['sources'] if s['shape']==[1024,1024])
            with np.load(ROOT/source['source']) as z:x=center(z['raw'],256).astype(np.int64);mask=center(z['mask'],256);x[mask]=0
            folder=target/stem;folder.mkdir(); commands=[]
            row=dict(id=stem,configuration=dict(family='baseline',config=cfg),status='EXCEPTION',
                     original_failure_preserved=True,body_sha256=replay['body_sha256'])
            try:
                path=previous/stem/'native.body'
                if sha(path)!=replay['body_sha256']:raise ValueError('Saved replay body changed')
                body=path.read_bytes(); decoded=roundback(body_codec(cfg,'decode',body,x.shape,commands,folder),mask)
                meta=dict(codec=cfg,geo=crop_geo(source['geo'],1024,256),units='m2',epsilons=list(EPSILONS),
                          output='float64_integer',postprocessor=POSTPROCESSOR,missing_zero=True,common_full_field_query_service=1)
                config=zlib.compress(json.dumps(meta,sort_keys=True,separators=(',',':')).encode(),9)
                mb=zlib.compress(np.packbits(mask.ravel(),bitorder='little').tobytes(),9) if mask.any() else b''
                payload=HEADER.pack(b'BA02',*x.shape,len(mb),len(config),len(body),digest(decoded,mask))+mb+config+body
                blob=payload+hashlib.sha256(payload).digest(); packet=folder/(stem+'.packet');packet.write_bytes(blob)
                y,m,p,d=endpoint.decode(packet)
                a=audit(x,y,mask,m,mask,p)
                eligible={str(e):legal(a,e) for e in BUDGETS}
                references={str(v['epsilon']):next(vv['baseline_bytes'] for vv in v['pairs'] if vv['site']==site)
                            for v in frontier if v['size']==256}
                changes={e:bool(v and len(blob)<references[e]) for e,v in eligible.items()}
                row.update(status='DECODED_AND_AUDITED',packet=str(packet.relative_to(ROOT)),packet_bytes=len(blob),
                    packet_sha256=sha(packet),fees=dict(header_bytes=HEADER.size,checksum_bytes=32,
                    mask_bytes=len(mb),config_bytes=len(config),body_bytes=len(body)),
                    decoder=d,audit=a,legal_at=eligible,improves_original_reference=changes)
            except Exception as e:row.update(error=str(e),traceback=traceback.format_exc())
            row['commands']=commands;rows.append(row);save(folder/'attempt.json',row)
    finally:endpoint.close()
    save(target/'ledger.json',dict(rows=rows))
    save(target/'report.json',dict(status='COMPLETE_SAVED_REPLAY_BODY_AUDIT',attempts=len(rows),
        sourcefree_decodes=sum(r['status']=='DECODED_AND_AUDITED' for r in rows),
        exceptions=sum(r['status']=='EXCEPTION' for r in rows),
        improved_reference_cells=sum(sum(r.get('improves_original_reference',{}).values()) for r in rows),
        original_22_failed_cells_unchanged=True,gpu_used=False))


if __name__=='__main__':run()
