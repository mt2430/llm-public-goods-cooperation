from pathlib import Path
import hashlib,json,shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,Normalize,to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text
from PIL import Image

import os
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/main_05_termination'
OUT=Path(os.environ.get('PGG_OUTPUT_DIR',str(ROOT/'reproduced')))/'main_05'
OUT.mkdir(parents=True,exist_ok=True)
files=['termination_trajectory_means.csv','random_round_source.csv','termination_summary.csv']
input_hashes={}
M=pd.read_csv(DATA/files[0]);Q=pd.read_csv(DATA/files[1]);S=pd.read_csv(DATA/files[2])
assert len(M)==683 and len(Q)==4668
models=['deepseek', 'kimi3', 'claude', 'glm52', 'gpt', 'gemini'];W,H=183,247
names={'kimi3':'Kimi','deepseek':'DeepSeek','claude':'Claude',
 'glm52':'GLM','gpt':'GPT','gemini':'Gemini'}
colors={.9:'#397A9A',1.02:'#C77A4F'}
cmaps={.9:LinearSegmentedColormap.from_list('blue',['#DDEBF2','#397A9A']),
       1.02:LinearSegmentedColormap.from_list('orange',['#F4E5D8','#C77A4F'])}
for cmap in cmaps.values():cmap.set_bad((0,0,0,0))
plt.rcParams.update({'font.family':'Arial','font.size':10,'axes.labelsize':10,'axes.titlesize':10,
 'xtick.labelsize':10,'ytick.labelsize':10,'axes.linewidth':.5,'text.color':'black','axes.labelcolor':'black',
 'axes.edgecolor':'black','xtick.color':'black','ytick.color':'black','axes.unicode_minus':True,
 'mathtext.fontset':'custom','mathtext.rm':'Arial','mathtext.it':'Arial:italic','mathtext.bf':'Arial:bold',
 'svg.fonttype':'none','pdf.fonttype':42,'figure.facecolor':'white','savefig.facecolor':'white','hatch.linewidth':.3})
def axmm(fig,x,y,w,h):return fig.add_axes([x/W,y/H,w/W,h/H])
def frame(ax):
    for spine in ax.spines.values():spine.set_visible(True);spine.set_color('black')
    ax.tick_params(direction='in',length=2,width=.45,pad=1.3,top=False,right=False)

fig=plt.figure(figsize=(W/25.4,H/25.4));order_rows=[];points=[];drawn=0
for i,model in enumerate(models):
    row,col=divmod(i,2);x=12+94*col;y=29+(2-row)*74
    fig.text(x/W,(y+61.5)/H,f'{chr(97+i)}  {names[model]}',fontsize=11,fontweight='bold')
    for j,r in enumerate([.9,1.02]):
        ax=axmm(fig,x+j*42,y+28,32,29)
        subset=M[M.model.eq(model)&M.R.eq(r)&M.regime.eq('random')].sort_values(['rounds','trajectory_id'])
        assert len(subset)==(27 if model=='kimi3' and r==.9 else 30)
        matrix=np.full((len(subset),52),np.nan)
        for display,(idx,tr) in enumerate(subset.iterrows()):
            q=Q[Q.slot_id.eq(tr.trajectory_id)].sort_values('round')
            assert q['round'].tolist()==list(range(1,int(tr['rounds'])+1))
            assert abs(q.contribution_rate.mean()-tr['mean'])<1e-12
            matrix[display,:len(q)]=q.contribution_rate.to_numpy()*100
            order_rows.append(dict(model=model,R=r,display_row=display+1,trajectory_id=tr.trajectory_id,
                                  observed_rounds=len(q),whole_run_mean=tr['mean']))
            drawn+=len(q)
        ax.set_facecolor('#FAFAFA');ax.patch.set_hatch('////');ax.patch.set_edgecolor('#D6D6D6')
        ax.imshow(np.ma.masked_invalid(matrix),cmap=cmaps[r],vmin=0,vmax=100,origin='upper',aspect='auto',
                  interpolation='nearest',extent=[.5,52.5,len(subset)+.5,.5])
        for k,length in enumerate(subset['rounds']):ax.plot([length+.5,length+.5],[k+.65,k+1.35],color='black',lw=.55)
        ax.set(xlim=(.5,53.5),ylim=(len(subset)+.5,.5),xticks=[1,10,30,50],yticks=[1,len(subset)])
        ax.set_xlabel('Round',labelpad=1)
        if j==0:ax.set_ylabel('Group',labelpad=2)
        ax.set_title(f'$R={r:.2f}$  $n={len(subset)}$',fontsize=10,loc='left',pad=3)
        frame(ax)
    ax=axmm(fig,x,y,74,21)
    for k,(r,regime) in enumerate([(.9,'fixed'),(.9,'random'),(1.02,'fixed'),(1.02,'random')]):
        sub=M[M.model.eq(model)&M.R.eq(r)&M.regime.eq(regime)].sort_values('trajectory_id')
        rng=np.random.default_rng(int.from_bytes(hashlib.sha256(f'{model}|{r}|{regime}|horizontal'.encode()).digest()[:8],'little'))
        jitter=rng.uniform(-.23,.23,len(sub))
        color='#99A2A7' if regime=='fixed' else colors[r]
        ax.scatter(k+jitter,sub['mean']*100,s=16,color=color,edgecolor='white',linewidth=.2,alpha=.85,zorder=2)
        summary=S[S.model.eq(model)&S.R.eq(r)&S.regime.eq(regime)&S.metric.eq('whole_run')].iloc[0]
        assert abs(summary['mean']-sub['mean'].mean())<1e-12
        p=summary['mean']*100
        ax.errorbar(k,p,yerr=[[p-summary.lo*100],[summary.hi*100-p]],fmt='D',ms=4.5,mec='white',mew=.25,
                    color='black',elinewidth=.65,capsize=2,capthick=.55,zorder=4)
        for t in sub.itertuples():points.append(dict(model=model,R=r,regime=regime,trajectory_id=t.trajectory_id,
                                                   mean=t.mean,x_jitter=float(jitter[list(sub.trajectory_id).index(t.trajectory_id)])))
    ax.set(xlim=(-.5,3.5),ylim=(-7,107),yticks=[0,50,100])
    ax.set_xticks(range(4),['Fixed\n0.90','Random\n0.90','Fixed\n1.02','Random\n1.02'],fontsize=10)
    ax.set_ylabel('Group mean (%)',labelpad=2);ax.axvline(1.5,color='#DDDDDD',lw=.5)
    frame(ax);ax.set_axisbelow(True);ax.grid(axis='y',color='#E8E8E8',lw=.3)

legend=[Line2D([],[],color='black',marker='|',ms=6,ls='none',label='Actual end'),
        Patch(facecolor='#FAFAFA',edgecolor='#D6D6D6',hatch='////',label='After termination'),
        Line2D([],[],marker='D',color='black',ms=4,ls='none',label='Mean and 95% CI')]
fig.legend(handles=legend,loc='lower center',bbox_to_anchor=(.5,16/H),ncol=3,frameon=False,
           fontsize=10,handlelength=1.3,columnspacing=2,borderpad=0,borderaxespad=0)
for j,r in enumerate([.9,1.02]):
    cax=axmm(fig,34+j*91,6,54,2)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,100),cmap=cmaps[r]),cax=cax,orientation='horizontal',ticks=[0,50,100])
    cb.ax.set_title(f'$R={r:.2f}$: contribution (%)',fontsize=9.5,pad=3)
    cb.ax.tick_params(direction='in',length=1.7,width=.45,pad=1,labelsize=9.5);cb.outline.set_linewidth(.45)
assert drawn==4668 and len(order_rows)==357 and len(points)==683
pd.DataFrame(order_rows).to_csv(OUT/'displayed_trajectory_order.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(points).to_csv(OUT/'displayed_group_points.csv',index=False,encoding='utf-8-sig')
fig.canvas.draw();renderer=fig.canvas.get_renderer();outside=[]
for t in fig.findobj(Text):
    if t.get_visible() and t.get_text().strip():
        assert to_rgba(t.get_color())[:3]==(0,0,0)
        b=t.get_window_extent(renderer)
        if b.x0<-.5 or b.y0<-.5 or b.x1>fig.bbox.width+.5 or b.y1>fig.bbox.height+.5:outside.append(t.get_text())
assert not outside,outside
for a,ax in enumerate(fig.axes):
    for other in fig.axes[a+1:]:assert not ax.bbox.overlaps(other.bbox)
stem='Figure_5'
fig.savefig(OUT/f'{stem}.pdf');fig.savefig(OUT/f'{stem}.svg')
fig.savefig(OUT/f'{stem}.png',dpi=600);fig.savefig(OUT/f'{stem}_preview.png',dpi=220)
plt.close(fig)
with Image.open(OUT/f'{stem}.png') as im:
    crop=im.crop((0,0,round(im.width*.51),round(im.height*.34)))
    crop.resize((1300,round(crop.height*1300/crop.width))).save(OUT/'Kimi_detail.png')
