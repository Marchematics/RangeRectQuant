"""Same-field coding and fixed-step sensitivity from saved source-free files.

Uses paper_plot_style.py, the attributed figures4papers adaptation, and the
shared-legend/aligned-panel convention of the user's reference figures.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from paper_plot_style import apply_publication_style,save_figure,plt,PALETTE

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'results/review_revision_20261002/report.json'


def main():
    data=json.loads(SOURCE.read_text())
    assert data['blocks']['representation']['decodes']==1280
    assert data['blocks']['step']['decodes']==128
    apply_publication_style()
    fig,axes=plt.subplots(1,3,figsize=(6,2.05))
    for e,color,marker in ((100,PALETTE['red_strong'],'s'),(1000,PALETTE['blue_main'],'o')):
        row=next(r for r in data['blocks']['representation']['budgets'] if r['epsilon']==e)
        x=np.arange(3);values=[row['bpp'][k] for k in ('direct','shuffled','split')]
        axes[0].bar(x+(-.18 if e==100 else .18),values,width=.34,color=color,
                    edgecolor='black',linewidth=.5,label=f'Budget {e} m²')
        groups=[r for r in data['blocks']['step']['groups'] if r['split']=='original-heldout' and r['epsilon']==e]
        assert len(groups)==8 and all(r['all_legal'] for r in groups)
        for ax,key,factor in ((axes[1],'bpp',1),(axes[2],'fine_fraction',100)):
            ax.plot(np.arange(8),[r[key]*factor for r in groups],color=color,marker=marker,
                    markersize=3,linewidth=1.1,label=f'Budget {e} m²')
    axes[0].set_xticks(np.arange(3),['Direct','Shuffled','Split']);axes[0].set_xlabel('Identical-field representation',fontsize=8)
    for ax in axes[1:]:
        ax.set_xticks([0,2,4,7],['16','8','5','2']);ax.set_xlabel('Step divisor',fontsize=8)
        ax.axvline(4,color='#666666',ls=':',lw=.8)
    for ax,title,label in zip(axes,('(a) Representation','(b) Coarse step','(c) Fine precision'),
                             ('Complete size (bits/pixel)','Complete size (bits/pixel)','Fine pixels (%)')):
        ax.set_title(title,fontsize=9);ax.set_ylabel(label,fontsize=8)
        ax.set_ylim(bottom=0);ax.grid(axis='y',color='#dddddd',linewidth=.45,ls=':');ax.set_axisbelow(True)
        ax.tick_params(labelsize=8,length=2.5)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=2,fontsize=9)
    fig.subplots_adjust(left=.09,right=.985,bottom=.28,top=.75,wspace=.53)
    destination=ROOT/'paper/figures/research/review_mechanism';save_figure(fig,destination)
    files=[SOURCE,Path(__file__),ROOT/'paper/plotting/paper_plot_style.py',destination.with_suffix('.pdf'),destination.with_suffix('.png')]
    receipt=dict(status='PASS_SAVED_DATA_ONLY',input_output_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                 representation_locations=40,step_locations=4,step_split='original-heldout',
                 step_default_divisor=5,reference='https://github.com/ChenLiu-1996/figures4papers',
                 reference_commit='f0bb7559abe90f5e1828797126d4d133c1bd47d7',reference_license='CC BY-NC 4.0')
    (ROOT/'paper/figures/research/provenance_review_mechanism.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':main()
