"""Export the protected-sample table from saved, independently decoded files."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'results/protected_sweep_20261002/ledger.json'
rows=json.loads(source.read_text())['rows']
if len(rows)!=40 or any(r['status']!='DECODED_AND_AUDITED' or not r['legal_at'][str(r['configuration']['epsilon'])] for r in rows):
    raise ValueError('Complete protected sweep required')
lines=[r'\begin{table}[t]',r'\centering',r'\caption{Protected-sample sweep at regional budgets 100 and 1000\,m$^2$. Fine fractions and complete sizes are means over four locations. Every file has zero range, integer, mask, and protected-value violations.}',r'\label{tab:protected}',r'\begin{tabular}{rrrrrrr}',r'\toprule',r' & \multicolumn{2}{c}{Fine pixels (\%)} & \multicolumn{2}{c}{Bits/pixel} & \multicolumn{2}{c}{Max. error / budget}\\',r'Protected (\%) & 100 & 1000 & 100 & 1000 & 100 & 1000\\',r'\midrule']
for f in (0,.001,.01,.05,.1):
    values=[]
    for metric in ('fine','bpp','error'):
        for e in (100,1000):
            group=[r for r in rows if r['configuration']['epsilon']==e and r['configuration']['protected_fraction']==f]
            if len(group)!=4: raise ValueError('Missing protected cell')
            val=(sum(100*r['mechanism']['off_lattice']/512**2 for r in group)/4 if metric=='fine'
                 else sum(8*r['packet_bytes']/512**2 for r in group)/4 if metric=='bpp'
                 else max(r['audit']['max_rectangle_error']/e for r in group))
            values.append(f'{val:.2f}')
    lines.append(f'{100*f:g} & '+' & '.join(values)+r'\\')
lines.extend([r'\bottomrule',r'\end{tabular}',r'\end{table}'])
target=ROOT/'paper/tables/protected_table.tex'
target.write_text('\n'.join(lines)+'\n')
receipt=dict(input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             table_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
             script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(ROOT/'paper/notes/protected_table_provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
