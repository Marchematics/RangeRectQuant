"""Post-hoc saved-field diagnosis, not additional optimizer runs or holdouts."""
import argparse
import json
from pathlib import Path
import numpy as np
from range_rect_quant.coarse_feasibility import coarse_row_feasible
from run_pilot import ROOT,sources,sha,write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise SystemExit('Refusing to overwrite diagnosis')
    records={r['site']:r for r in sources()};rows=[]
    for row in json.loads((a.source/'ledger.json').read_text()):
        if row['mode']=='identity':continue
        source=records[row['site']];x=source['x'];mask=source['mask']
        if sha(ROOT/row['output'])!=row['output_sha256']:raise ValueError('Frozen decoded artifact')
        with np.load(ROOT/row['output'],allow_pickle=False) as z:y=z['y'].astype(np.int64)
        step=row['step'];band=25 if step==20 else 250
        prefix=(y-x).cumsum(0).cumsum(1);fine=(y%step!=0).sum(1);blocked=[]
        protected=mask|((x==0)&~mask) if row['mode']=='zero-preserve' else mask
        if fine.tolist()!=row['quantizer']['row_min_off_lattice']:raise ValueError('Saved row objective counts')
        for i in range(len(x)):
            up=prefix[i-1] if i else np.zeros(x.shape[1],np.int64)
            result=coarse_row_feasible(x[i],up,band,step,10000,protected[i])
            if result['feasible']!=(fine[i]==0):raise ValueError('Conditional zero-fine certificate disagrees')
            if not result['feasible']:blocked.append(dict(row=i,first_blocked_column=result['first_blocked_column'],reason=result['reason']))
        xt=x.reshape(256,2,256,2);yt=y.reshape(256,2,256,2)
        # Tile row sums: sum within the final axis; column sums: sum within axis1.
        changed_rows=np.any(xt.sum(3)!=yt.sum(3),axis=1)
        changed_columns=np.any(xt.sum(1)!=yt.sum(1),axis=2)
        changed_margins=int((changed_rows|changed_columns).sum())
        rows.append(dict(id=row['id'],output_sha256=row['output_sha256'],fine=int(fine.sum()),
            rows_with_fine=len(blocked),all_512_fixed_incoming_coarse_verdicts_match=True,
            conditional_coarse_obstructions=blocked,tiles_with_changed_row_or_column_margins=changed_margins,
            total_tiles=65536,positive_to_zero=int(np.count_nonzero((x>0)&(y==0))),
            zero_to_positive=int(np.count_nonzero((x==0)&~mask&(y>0)))))
    write_json(a.out,dict(status='PASS_SAVED_CONDITIONAL_DIAGNOSIS',cases=rows,
        fixed_incoming_rows_checked=512*len(rows),script_sha256=sha(Path(__file__)),
        source_report_sha256=sha(a.source/'report.json'),posthoc_descriptive_not_preregistered_prediction=True,
        global_fine_minimality_established=False,new_optimizer_runs=0,new_sources=0))
    print('PASS',len(rows),'saved fields;',512*len(rows),'fixed-incoming row feasibility checks')


if __name__=='__main__':main()
