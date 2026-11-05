"""Publication grids for group size and paired reasoning settings."""
from pathlib import Path
import json,hashlib,string,sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
import os
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/main_06_07'
OUT=Path(os.environ.get('PGG_OUTPUT_DIR',str(ROOT/'reproduced')))/'main_06_07'
OUT.mkdir(parents=True,exist_ok=True)
P=OUT;S=DATA
MODELS=[('deepseek_reasoning_enabled','DeepSeek'),('kimi_reasoning_enabled','Kimi'),('claude_reasoning_enabled','Claude'),('glm_reasoning_enabled','GLM'),('gpt_reasoning_enabled','GPT'),('gemini_reasoning_enabled','Gemini')]
ARMS=['none','once_public','each_public'];COLORS=['#99A2A7','#397A9A','#C77A4F'];MARKERS=['o','o','s']
NS=[4,6,8,12];W=183
plt.rcParams.update({'font.family':'Arial','font.size':10,'axes.labelsize':10,'axes.titlesize':11,'xtick.labelsize':9.5,'ytick.labelsize':9.5,'axes.linewidth':.65,'text.color':'black','axes.labelcolor':'black','axes.edgecolor':'black','xtick.color':'black','ytick.color':'black','svg.fonttype':'none','pdf.fonttype':42,'mathtext.fontset':'dejavusans','savefig.facecolor':'white','legend.frameon':False})
reports=[]
def axis(fig,x,y,w,h,H):return fig.add_axes([x/W,y/H,w/W,h/H])
def style(ax):
    for sp in ax.spines.values():sp.set_visible(True);sp.set_color('black')
    ax.tick_params(direction='in',top=False,right=False,length=2.5,width=.65,pad=2.2)
    ax.set_axisbelow(True);ax.grid(axis='y',color='#E6E9EA',lw=.45)
def save(fig,stem):
    fig.canvas.draw();ren=fig.canvas.get_renderer();outside=[];overlaps=[]
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip():continue
        b=t.get_window_extent(ren)
        if b.x0<-.7 or b.y0<-.7 or b.x1>fig.bbox.width+.7 or b.y1>fig.bbox.height+.7:outside.append(t.get_text())
    for ax in fig.axes:
        labels=[t for t in ax.get_xticklabels() if t.get_visible()]
        for a,b in zip(labels,labels[1:]):
            if a.get_window_extent(ren).overlaps(b.get_window_extent(ren)):overlaps.append([a.get_text(),b.get_text()])
    assert not outside,(stem,outside)
    assert not overlaps,(stem,overlaps)
    for ext in ['pdf','svg']:fig.savefig(P/f'{stem}.{ext}')
    fig.savefig(P/f'{stem}.png',dpi=600);fig.savefig(P/f'{stem}_preview.png',dpi=220)
    reports.append({'figure':stem,'size_mm':(np.asarray(fig.get_size_inches())*25.4).round(2).tolist(),'axes':len(fig.axes),'outside_text':outside,'overlapping_adjacent_xlabels':overlaps,'sha256':hashlib.sha256((P/f'{stem}.pdf').read_bytes()).hexdigest()})
    plt.close(fig)
if '--figure-7-only' not in sys.argv:
    s=pd.read_csv(S/'Figure_6_summary.csv');s=s[s.metric.eq('mean')]
    H=119;fig=plt.figure(figsize=(W/25.4,H/25.4))
    for i,(cfg,name) in enumerate(MODELS):
        ax=axis(fig,14+(i%3)*57,73 if i<3 else 20,49,34,H)
        for j,arm in enumerate(ARMS):
            z=s[s.configuration_id.eq(cfg)&s.communication.eq(arm)].sort_values('N');assert len(z)==4
            y=z.estimate.to_numpy();err=np.maximum(0,np.array([y-z.lo.to_numpy(),z.hi.to_numpy()-y]))
            ax.errorbar(z.N,y,yerr=err,fmt=MARKERS[j],color=COLORS[j],ms=6.2 if j else 5.8,mec='white',mew=.5,lw=.7,ls=(0,(3,2)),elinewidth=.85,capsize=2,capthick=.7,zorder=4+j)
        ax.set(xlim=(3.5,12.5),ylim=(-5,105),xticks=NS,yticks=[0,50,100]);style(ax)
        ax.set_title(f'{string.ascii_lowercase[i]}  {name}',loc='left',fontsize=11,fontweight='bold',pad=6)
        if i%3==0:ax.set_ylabel('Contribution (%)',labelpad=3)
        if i>=3:ax.set_xlabel('Group size $N$',labelpad=3)
        if i==5:
            handles=[Line2D([],[],color=COLORS[k],marker=MARKERS[k],ms=5.5,lw=.7,ls='--',label=l) for k,l in enumerate(['No communication','First-round public','Every-round public'])]
            ax.legend(handles=handles,loc='center',bbox_to_anchor=(.49,.40),fontsize=8.4,handlelength=1.2,handletextpad=.4,labelspacing=.4)
    save(fig,'Figure_6')
c=pd.read_csv(S/'Figure_7_conditions.csv')
pairs=[('DeepSeek','deepseek_reasoning_disabled','deepseek_reasoning_enabled'),('Claude','claude_reasoning_disabled','claude_reasoning_enabled'),('GPT','gpt_reasoning_disabled','gpt_reasoning_enabled')]
H=156;fig=plt.figure(figsize=(W/25.4,H/25.4))
for i,(name,off,on) in enumerate(pairs):
    for j,n in enumerate(NS):
        ax=axis(fig,14+j*42,112-i*44,37,29,H)
        for k,cfg in enumerate([off,on]):
            z=c[c.configuration_id.eq(cfg)&c.N.eq(n)].sort_values('R');assert len(z)==11
            color=COLORS[k];marker=['o','s'][k];x=z.R.to_numpy();y=z['mean'].to_numpy()*100
            ax.fill_between(x,z.mean_lo.to_numpy()*100,z.mean_hi.to_numpy()*100,color=color,alpha=.17,lw=0)
            ax.plot(x,y,color=color,marker=marker,ms=4.7,mec='white',mew=.35,lw=.6,ls=(0,(2,2)))
        ax.set(xlim=(.37,1.23),ylim=(-5,105),xticks=[.4,.8,1.,1.2],xticklabels=['0.4','0.8','1.0','1.2'],yticks=[0,50,100]);style(ax)
        ax.axvline(1,color='#777777',lw=.65,ls=(0,(3,3)),zorder=0)
        if j>0:ax.tick_params(labelleft=False)
        ax.set_title(string.ascii_lowercase[j]+str(i+1)+('  '+name if j==0 else ''),loc='left',fontsize=10.5,fontweight='bold',pad=4)
        if i==0:fig.text((14+j*42+18.5)/W,151/H,f'$N={n}$',fontsize=10.5,ha='center',va='center')
fig.text(3/W,84/H,'Whole-run contribution (%)',rotation=90,ha='center',va='center',fontsize=10)
fig.text(.53,13/H,'Normalized synergy $R$',ha='center',va='center',fontsize=10)
handles=[Line2D([],[],color=COLORS[k],marker=['o','s'][k],ms=5.5,lw=.6,ls='--',label=l) for k,l in enumerate(['Reasoning disabled','Reasoning enabled'])]
fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.53,1.5/H),ncol=2,fontsize=9.5,handlelength=1.7,columnspacing=2.4)
save(fig,'Figure_7')
if '--figure-7-only' in sys.argv and (P/'figure_verification.json').exists():
    previous=json.loads((P/'figure_verification.json').read_text(encoding='utf8'))
    reports=[r for r in previous if r['figure']!='Figure_7']+reports
(P/'figure_verification.json').write_text(json.dumps(reports,indent=2),encoding='utf8')
print(json.dumps(reports,indent=2))
