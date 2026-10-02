"""Saved-data multi-panel plots; shared legends and fixed method colors.

Layout follows the user's two figure references: aligned small multiples,
shared legends and connected trends. Styling/code patterns adapt
figures4papers figure_VIGIL/plot_ablation.py and
figure_ophthal_review/plot_trend.py, at the pinned repository commit in
paper_plot_style.py (CC BY-NC 4.0). No reference numerical data are reused.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from paper_plot_style import apply_publication_style,save_figure,plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'paper/figures/research'
COLORS={'RangeRectQuant':'#0F4D92','fixed-margin':'#D88F8A','sz3':'#4EA6A0',
        'mgard':'#8C80B1','qpet':'#8EAD03','lossless':'#767676'}
LABELS={'RangeRectQuant':'RangeRectQuant','fixed-margin':'Fixed margin','sz3':'SZ3',
        'mgard':'MGARD','qpet':'QPET','lossless':'Exact reconstruction'}
MARKERS={'RangeRectQuant':'o','fixed-margin':'s','sz3':'v','mgard':'^','qpet':'D','lossless':'x'}
INPUTS={}


def read(path):
    path=ROOT/path; INPUTS[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text())


def axes_style(ax):
    ax.grid(axis='y',color='#d5d5d5',linewidth=.45,linestyle=':')
    ax.set_axisbelow(True); ax.tick_params(labelsize=8,length=2.5,width=.7)


def frontier():
    data=read('results/expanded_frontier_20261002/report.json')
    if (data['status']!='COMPLETE_FIXED_40_LOCATION_MATRIX' or
        any(r['qualifying_locations']['RangeRectQuant']!=40 for r in data['frontier'])):
        raise ValueError('Plot requires complete fixed matrix and forty verified main files at every point')
    fig,axes=plt.subplots(1,3,figsize=(6,2.25),sharey=True)
    for ax,size in zip(axes,(256,512,1024)):
        rows=[r for r in data['frontier'] if r['size']==size]
        for method in COLORS:
            x=[r['epsilon'] for r in rows]
            y=[r['bpp'][method] if r['bpp'][method] is not None else np.nan for r in rows]
            ax.plot(x,y,color=COLORS[method],marker=MARKERS[method],markersize=3,
                    linewidth=1.3 if method=='RangeRectQuant' else .9,label=LABELS[method])
        ax.set_xscale('log'); ax.set_xticks([25,100,500,5000],['25','100','500','5000'])
        ax.set_ylim(bottom=0); ax.set_title(f'{size} × {size}',fontsize=10)
        ax.set_xlabel('Regional sum budget (m²)',fontsize=8); axes_style(ax)
    axes[0].set_ylabel('Complete size (bits/pixel)',fontsize=9)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,1),ncol=3,
               fontsize=8,columnspacing=1.2,handlelength=2)
    fig.subplots_adjust(left=.10,right=.98,bottom=.23,top=.72,wspace=.12)
    save_figure(fig,OUT/'frontier')


def protected():
    report=read('results/protected_sweep_20261002/report.json')
    rows=read('results/protected_sweep_20261002/ledger.json')['rows']
    if report['joint_valid']!=40 or report['exceptions']:
        raise ValueError('Complete verified protected sweep required')
    timing=read('results/protected_timing_20261002/report.json')
    times={r['id']:r['median_seconds'] for r in timing['rows']}
    fig,axes=plt.subplots(1,3,figsize=(6,2.7))
    fractions=[0,.001,.01,.05,.1]
    for e,color,marker in ((100,'#D88F8A','s'),(1000,'#0F4D92','o')):
        matrix=[[r for r in rows if r['configuration']['epsilon']==e and
                 r['configuration']['protected_fraction']==f] for f in fractions]
        metrics=[lambda r:8*r['packet_bytes']/512**2,
                 lambda r:100*r['mechanism']['off_lattice']/512**2,
                 lambda r:times[r['id']]]
        for ax,metric in zip(axes,metrics):
            # Means over four locations; no fabricated seed uncertainty.
            values=[np.mean([metric(r) for r in group]) for group in matrix]
            ax.plot(np.array(fractions)*100,values,color=color,marker=marker,
                    linewidth=1.2,markersize=3,label=f'Budget {e} m²')
            ax.set_xlabel('Protected samples (%)',fontsize=8)
            ax.set_xticks([0,1,5,10]); axes_style(ax)
    for ax,label in zip(axes,('Complete size\n(bits/pixel)','Fine pixels (%)','Construction + audit (s)')):
        # Set bounds after both budgets so the second curve cannot be clipped.
        ax.relim(); ax.autoscale_view(); ax.margins(y=.08); ax.set_ylim(bottom=0)
        ax.set_ylabel(label,fontsize=8)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',ncol=2,fontsize=9)
    fig.subplots_adjust(left=.10,right=.98,bottom=.21,top=.81,wspace=.58)
    save_figure(fig,OUT/'protected')


def closest():
    report=read('results/closest_mechanism_20261002/report.json')
    rows=read('results/closest_mechanism_20261002/ledger.json')['rows']
    if report['sourcefree_decodes']!=56 or report['exceptions']:
        raise ValueError('Complete closest-mechanism evidence required')
    methods=['sigma-delta','sigma-delta-clip','sigma-delta-clip-integer','sigma-delta-project',
             'prefix-round','prefix-round-clip','RangeRectQuant']
    names=['Stable sigma–delta','Sigma–delta + clip','Sigma–delta + clip + integer',
           'Projected sigma–delta','Prefix rounding','Prefix rounding + clip','RangeRectQuant']
    colors=['#4EA6A0','#D88F8A','#B64342','#8C80B1','#8EAD03','#BD9B3F','#0F4D92']
    fig,axes=plt.subplots(1,2,figsize=(6,2.2))
    x=np.arange(7)
    for e,shift,hatch in ((100,-.18,'///'),(1000,.18,None)):
        grouped=[[r for r in rows if r['configuration']==dict(family=m,epsilon=e)] for m in methods]
        worst=[max(r['audit']['max_rectangle_error']/e for r in group) for group in grouped]
        bpp=[8*sum(r['packet_bytes'] for r in group)/(4*512**2) for group in grouped]
        for ax,values in zip(axes,(worst,bpp)):
            ax.bar(x+shift,values,width=.33,color=colors,hatch=hatch,edgecolor='black',linewidth=.4)
        for group,i in zip(grouped,x):
            if not all(r['legal_at'][str(e)] for r in group):
                axes[1].plot(i+shift,bpp[i]+.12,'x',color='black',markersize=4,markeredgewidth=.7)
    axes[0].axhline(1,color='black',linestyle='--',linewidth=.8)
    axes[0].set_yscale('log'); axes[0].set_ylabel('Worst regional error\n/ budget',fontsize=9)
    axes[1].set_ylabel('Complete size\n(bits/pixel)',fontsize=9); axes[1].set_ylim(bottom=0)
    for ax in axes:
        ax.set_xticks(x,[str(i+1) for i in x]); ax.set_xlabel('Construction',fontsize=9); axes_style(ax)
    from matplotlib.patches import Patch
    handles=[Patch(facecolor='white',edgecolor='black',hatch='///',label='Budget 100 m²'),
             Patch(facecolor='white',edgecolor='black',label='Budget 1000 m²')]
    fig.legend(handles=handles,loc='upper center',ncol=2,fontsize=9)
    # Numbered method labels are defined on the same figure, not an external key.
    fig.text(.07,.015,'  '.join(f'{i+1}: {name}' for i,name in enumerate(names[:2]))+'\n'+
             '  '.join(f'{i+3}: {name}' for i,name in enumerate(names[2:4]))+'\n'+
             '  '.join(f'{i+5}: {name}' for i,name in enumerate(names[4:])),fontsize=7.4,linespacing=1.5)
    fig.subplots_adjust(left=.10,right=.98,bottom=.41,top=.83,wspace=.4)
    save_figure(fig,OUT/'closest')


def mechanism():
    path=ROOT/'results/closest_mechanism_20261002/mechanism_example.npz'
    INPUTS[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    with np.load(path,allow_pickle=False) as z:
        x,y,widths,p=(z[k] for k in ('x','y','widths','protected'))
    fine=(y%200!=0)&~p
    fig,axes=plt.subplots(1,3,figsize=(6,2.4))
    source=axes[0].imshow(x,cmap='viridis',vmin=0,vmax=10000,rasterized=True)
    axes[0].set_title('Source built area',fontsize=9)
    prefix=(y-x).cumsum(0).cumsum(1)
    error=axes[1].imshow(prefix,cmap='RdBu_r',vmin=-250,vmax=250,rasterized=True)
    axes[1].set_title('Prefix error',fontsize=9)
    width=axes[2].imshow(widths,cmap='Greys_r',vmin=0,vmax=501,rasterized=True)
    rr,cc=np.where(fine); axes[2].scatter(cc,rr,s=.6,c='#B64342',alpha=.8,rasterized=True)
    axes[2].set_title('Feasible width + fine pixels',fontsize=8)
    for ax in axes: ax.set_xticks([]); ax.set_yticks([])
    for ax,artist,label,ticks in zip(axes,(source,error,width),('Built area (m²)','Prefix error (m²)','Allowed integer states'),
                                   ([0,5000,10000],[-250,0,250],[0,250,501])):
        bar=fig.colorbar(artist,ax=ax,orientation='horizontal',fraction=.07,pad=.035,ticks=ticks)
        bar.ax.tick_params(labelsize=6.5,length=2); bar.set_label(label,fontsize=7)
    fig.text(.045,.015,'Cairo; budget 1000 m²; coarse step 200 m². Red: unprotected fine pixels.',fontsize=8)
    fig.subplots_adjust(left=.04,right=.96,bottom=.20,top=.90,wspace=.32)
    save_figure(fig,OUT/'mechanism')


def water():
    data=read('results/water_frontier_20261002/report.json')
    if data['sourcefree_decodes']!=392 or data['exceptions']:
        raise ValueError('Complete water matrix required')
    fig,axes=plt.subplots(1,2,figsize=(6,2.55))
    rows=data['comparisons']; budgets=[r['epsilon'] for r in rows]
    for key,name,color,marker in (('main_bytes','RangeRectQuant','#0F4D92','o'),
                                 ('baseline_bytes','Best eligible external file','#767676','s')):
        totals=[sum(p[key] for p in r['pairs']) for r in rows]
        axes[0].plot(budgets,np.array(totals)*8/(8*512**2),color=color,marker=marker,
                     markersize=3,linewidth=1.2,label=name)
    axes[1].plot(budgets,[100*r['reduction_fraction'] for r in rows],color='#0F4D92',marker='o',markersize=3,linewidth=1.2)
    axes[1].axhline(0,color='#767676',linestyle='--',linewidth=.7)
    for ax in axes:
        ax.set_xscale('log'); ax.set_xticks([5,25,100,1000],['5','25','100','1000'])
        ax.set_xlabel('Regional sum budget (percentage points)',fontsize=8); axes_style(ax)
    axes[0].set_ylabel('Complete size (bits/pixel)',fontsize=9); axes[0].set_ylim(bottom=0)
    axes[1].set_ylabel('Complete-size reduction (%)',fontsize=9)
    handles,labels=axes[0].get_legend_handles_labels(); fig.legend(handles,labels,loc='upper center',ncol=2,fontsize=8)
    fig.subplots_adjust(left=.10,right=.98,bottom=.22,top=.80,wspace=.43)
    save_figure(fig,OUT/'water')


def scaling():
    data=read('results/runtime_scaling_20261002/report.json')
    if data['status']!='COMPLETE_ATTEMPTED_SCALING' or data['exceptions']:
        raise ValueError('Completed scaling required')
    fig,axes=plt.subplots(1,3,figsize=(6,2.9))
    for method,color,marker in (('RangeRectQuant','#0F4D92','o'),('Exact row search','#D88F8A','s'),('Fixed margin','#767676','^')):
        selected=[r for r in data['rows'] if r['method']==method and r['epsilon']==100]
        measured=[r for r in selected if r['status']=='MEASURED']
        metrics=[lambda r:np.median(r['encode_seconds']),lambda r:np.median(r['decode_seconds']),
                 lambda r:r['process_peak_rss_bytes']/2**20]
        for ax,metric in zip(axes,metrics):
            ax.plot([r['size'] for r in measured],[metric(r) for r in measured],color=color,
                    marker=marker,markersize=3,linewidth=1.1,label=method)
            ax.set_xscale('log',base=2); ax.set_yscale('log'); ax.set_xticks([256,1024,4096],['256','1024','4096'])
            ax.set_xlabel('Field width (pixels)',fontsize=8); axes_style(ax)
    for ax,label in zip(axes,('Complete encoding (s)','Decoding (s)','Peak process memory (MiB)')):
        ax.set_ylabel(label,fontsize=8)
    from matplotlib.ticker import FuncFormatter
    for ax in axes[:2]: ax.yaxis.set_major_formatter(FuncFormatter(lambda value,_:f'{value:g}'))
    axes[2].set_yscale('linear'); axes[2].set_ylim(bottom=0); axes[2].set_yticks([0,500,1000,1500])
    handles,labels=axes[0].get_legend_handles_labels(); fig.legend(handles,labels,loc='upper center',ncol=3,fontsize=8)
    fig.subplots_adjust(left=.10,right=.98,bottom=.19,top=.79,wspace=.63)
    save_figure(fig,OUT/'scaling')


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('figures',nargs='+',choices=['frontier','protected','closest','mechanism','scaling','water'])
    args=parser.parse_args(); apply_publication_style()
    for name in args.figures: globals()[name]()
    OUT.mkdir(parents=True,exist_ok=True)
    receipt=OUT/('provenance_'+'_'.join(args.figures)+'.json')
    outputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
             for name in args.figures for p in (OUT/(name+'.pdf'),OUT/(name+'.png'))}
    receipt.write_text(json.dumps(dict(inputs=INPUTS,outputs=outputs,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        reference_repo='https://github.com/ChenLiu-1996/figures4papers',reference_commit='f0bb7559abe90f5e1828797126d4d133c1bd47d7',
        reference_license='CC-BY-NC-4.0',user_layout_reference='shared legends, aligned small multiples, connected trends',
        fabricated_results=False),indent=2)+'\n')
