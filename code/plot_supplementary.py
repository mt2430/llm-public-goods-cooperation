"""Redraw the four supplementary figures from their frozen source tables."""
from pathlib import Path
import hashlib,json,shutil,string
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.ticker import FormatStrFormatter
from PIL import Image,ImageOps,ImageDraw

import os
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/supplementary'
OUT=Path(os.environ.get('PGG_OUTPUT_DIR',str(ROOT/'reproduced')))/'supplementary'
OUT.mkdir(parents=True,exist_ok=True)
B=OUT;P=DATA;O=OUT
files=['S1_communication_contrasts.csv', 'S2_group_outcomes_R090.csv', 'S2_group_summary.csv', 'S3_horizon_information.csv', 'S3_task_contrasts.csv']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={f:sha(P/f) for f in files}
F=pd.read_csv(P/files[0]);G=pd.read_csv(P/files[1]);A=pd.read_csv(P/files[3]);E=pd.read_csv(P/files[4])
assert len(F)==54 and len(G)==483 and len(A)==60 and len(E)==30
MODELS=[('deepseek_reasoning_enabled','DeepSeek'),('kimi_reasoning_enabled','Kimi'),
        ('claude_reasoning_enabled','Claude'),('glm_reasoning_enabled','GLM'),
        ('gpt_reasoning_enabled','GPT'),('gemini_reasoning_enabled','Gemini')]
GREY='#99A2A7';BLUE='#397A9A';ORANGE='#C77A4F';DARK='#59666C'
COL=[GREY,BLUE,ORANGE]; ARMS=['none','once_public','each_public']
RN=[.6,.9,.98,1.,1.02];RC=[GREY,BLUE,'#83AEC1','#B68A4B',ORANGE]
plt.rcParams.update({'font.family':'Arial','font.size':9.3,'axes.labelsize':9.3,
 'axes.titlesize':10.8,'xtick.labelsize':8.5,'ytick.labelsize':8.5,
 'axes.linewidth':.65,'text.color':'black','axes.labelcolor':'black',
 'axes.edgecolor':'black','xtick.color':'black','ytick.color':'black',
 'svg.fonttype':'none','pdf.fonttype':42,'mathtext.fontset':'dejavusans',
 'savefig.facecolor':'white','legend.frameon':False})
reports=[]

def style(ax,grid='y'):
    ax.tick_params(direction='in',length=3,width=.65,top=False,right=False,pad=3)
    for s in ax.spines.values():s.set_visible(True);s.set_color('black')
    ax.set_axisbelow(True)
    if grid:ax.grid(axis=grid,color='#E5E8EA',lw=.45)

def title(ax,letter,name):
    ax.set_title(f'{letter}  {name}',loc='left',fontweight='bold',pad=7)

def err(ax,x,mean,lo,hi,color,marker='o',horizontal=False,**kw):
    e=np.maximum(0,np.array([np.asarray(mean)-lo,np.asarray(hi)-mean]))
    args=dict(fmt=marker,color=color,ms=5.2,mec='white',mew=.45,
              elinewidth=.8,capsize=2.1,capthick=.7,zorder=4)
    args.update(kw)
    if horizontal:return ax.errorbar(mean,x,xerr=e,**args)
    return ax.errorbar(x,mean,yerr=e,**args)

def save(fig,name,records,notes):
    fig.canvas.draw();ren=fig.canvas.get_renderer();outside=[]
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip():continue
        box=t.get_window_extent(ren)
        if box.x0<-.8 or box.y0<-.8 or box.x1>fig.bbox.width+.8 or box.y1>fig.bbox.height+.8:outside.append(t.get_text())
    if outside:raise AssertionError((name,'outside text',outside))
    for ext in ['pdf','svg']:fig.savefig(O/(name+'.'+ext))
    fig.savefig(O/(name+'.png'),dpi=600)
    fig.savefig(O/(name+'_preview.png'),dpi=200)
    reports.append({'figure':name,'size_mm':(np.array(fig.get_size_inches())*25.4).round(2).tolist(),
                    'records':records,'axes':len(fig.axes),'outside_text':outside,'notes':notes})
    plt.close(fig)

# S2: compare the window profile directly within each model.
fig,axs=plt.subplots(2,3,figsize=(183/25.4,137/25.4))
fig.subplots_adjust(left=.085,right=.985,top=.91,bottom=.18,hspace=.37,wspace=.22)
cons=['first_minus_none','every_minus_none','every_minus_first']
cc=[BLUE,ORANGE,DARK];marks=['o','s','^'];metrics=['whole_run','late_stage','final_round']
used=[]
for i,(cfg,name) in enumerate(MODELS):
    ax=axs.flat[i]
    for k,con in enumerate(cons):
        z=F[F.configuration_id.eq(cfg)&F.contrast.eq(con)].set_index('metric').loc[metrics]
        used.extend(z.index.tolist())
        x=np.arange(3)+(k-1)*.045
        err(ax,x,z.estimate_pp.to_numpy(),z.lo_pp.to_numpy(),z.hi_pp.to_numpy(),cc[k],marks[k],ls=(0,(2,2)),lw=.7)
    ax.set(xlim=(-.22,2.22),ylim=(-5,105),xticks=[0,1,2],yticks=[0,25,50,75,100])
    ax.set_xticklabels(['Whole','Late','Final'])
    if i%3==0:ax.set_ylabel('Contribution difference (pp)')
    else:ax.tick_params(labelleft=False)
    title(ax,string.ascii_lowercase[i],name);style(ax)
    ax.axhline(0,color='#777777',lw=.6)
fig.legend(handles=[Line2D([],[],color=c,marker=m,ms=5.5,ls='--',lw=.7,label=l) for c,m,l in
                    zip(cc,marks,['First − none','Every − none','Every − first'])],
           loc='lower center',bbox_to_anchor=(.52,.045),ncol=3,columnspacing=1.5,handletextpad=.5)
save(fig,'Figure_S1',len(used),'All 54 existing contrasts with unchanged intervals; discrete outcome windows, not chronological samples.')

# S3: retain observations and expose their empirical distributions without KDE.
fig=plt.figure(figsize=(183/25.4,153/25.4))
outer=fig.add_gridspec(3,2,left=.075,right=.985,bottom=.105,top=.935,hspace=.33,wspace=.28)
counts=[];swarm_records=[]
for i,(cfg,name) in enumerate(MODELS):
    inner=outer[i//2,i%2].subgridspec(1,2,width_ratios=[1.40,1],wspace=.30)
    ax=fig.add_subplot(inner[0]);ec=fig.add_subplot(inner[1])
    ax.set(xlim=(-16,116),ylim=(2.65,-.65),xticks=[0,50,100],yticks=[0,1,2])
    ax.set_yticklabels(['None','First','Every'],fontsize=8)
    ec.set(xlim=(-5,105),ylim=(-.03,1.03),xticks=[0,50,100],yticks=[0,.5,1])
    ec.set_yticklabels(['0','50','100']);ec.tick_params(axis='y',labelsize=7.5)
    title(ax,string.ascii_lowercase[i],name)
    ec.set_title('Cumulative (%)',loc='center',fontsize=8.1,pad=8)
    style(ax,grid='x');style(ec,grid='y')
    fig.canvas.draw()
    for k,arm in enumerate(ARMS):
        z=G[G.configuration_id.eq(cfg)&G.communication.eq(arm)].sort_values(['atlas_mean','trajectory_id'])
        values=z.atlas_mean.to_numpy()*100
        counts.append(len(values))
        # A discrete frequency strip (5 percentage-point bins); ECDF stays exact.
        edges=np.arange(0,105,5,dtype=float)
        nn,_=np.histogram(values,bins=edges)
        centers=(edges[1:]+edges[:-1])/2
        un=centers[nn>0];n=nn[nn>0]
        placed=[];offsets=[]
        for value,count in zip(un,n):
            xp=ax.transData.transform((value,k))[0]
            radius=np.sqrt(10*count)*fig.dpi/72/2
            candidates=[0]+[sign*step*1.4 for step in range(1,100) for sign in [1,-1]]
            chosen=next(off for off in candidates if all((xp-x0)**2+(off-y0)**2 >= (radius+r0+1)**2 for x0,y0,r0 in placed))
            placed.append((xp,chosen,radius))
            ybase=ax.transData.transform((value,k))[1]
            yp=ax.transData.inverted().transform((xp,ybase+chosen))[1]
            offsets.append(yp)
        assert max(abs(np.array(offsets)-k),default=0)<.47,(name,arm,'swarm overflow')
        ax.scatter(un,offsets,s=10*n,color=COL[k],alpha=.85,edgecolors='white',linewidths=.4,zorder=4)
        for value,yp,count in zip(un,offsets,n):
            if count>=3:ax.text(value,yp,str(count),ha='center',va='center',fontsize=6.3,color='white' if k==1 else 'black',zorder=5)
        q1,med,q3=np.quantile(values,[.25,.5,.75])
        ax.plot([q1,q3],[k+.42,k+.42],color='black',lw=1.6,solid_capstyle='butt',zorder=5)
        ax.plot(med,k+.42,marker='|',ms=6,color='black',mew=1.15,zorder=6)
        exact,nexact=np.unique(values,return_counts=True)
        cum=np.cumsum(nexact)/len(values)
        ec.step(np.r_[-5,exact,105],np.r_[0,cum,1],where='post',color=COL[k],lw=1.15,zorder=3+k)
        lookup=dict(zip(un,offsets))
        for tid,v in zip(z.trajectory_id,values):
            center=centers[min(int(v//5),19)]
            swarm_records.append({'trajectory_id':tid,'value_percent':v,'display_x':center,'display_y':lookup[center]})
    if i>=4:
        ax.set_xlabel('Contribution (%)');ec.set_xlabel('Contribution (%)')
fig.text(.53,.035,'Frequency dots: 5 pp bins     Black mark: median and interquartile range',ha='center',fontsize=8.5)
assert sum(counts)==483 and len({r['trajectory_id'] for r in swarm_records})==483
pd.DataFrame(swarm_records).to_csv(B/'swarm_display_coordinates.csv',index=False)
save(fig,'Figure_S2',sum(counts),'All 483 groups represented in 5-pp frequency bins with count-proportional marker areas; median, IQR and ECDF use exact unbinned values. No smoothing.')

# S4: an aligned interval matrix separates overlapping R profiles.
levels=[('horizon','1.0','T = 1'),('horizon','5.0','T = 5'),('horizon','10.0','T = 10'),
 ('horizon','20.0','T = 20'),('horizon','50.0','T = 50'),
 ('feedback_memory','No feedback / no history','No feedback / history'),
 ('feedback_memory','Aggregate / 1','Aggregate / 1'),('feedback_memory','Aggregate / 3','Aggregate / 3'),
 ('feedback_memory','Aggregate / all','Aggregate / all'),('feedback_memory','Individual / 1','Individual / 1'),
 ('feedback_memory','Individual / 3','Individual / 3'),('feedback_memory','Individual / all','Individual / all')]
rows=[('endowment','10.0','$E$: 10 vs 20'),('endowment','100.0','$E$: 100 vs 20'),
 ('action_resolution','0.001','Step/$E$: 0.001 vs 0.05'),('action_resolution','0.01','Step/$E$: 0.01 vs 0.05'),
 ('action_resolution','0.1','Step/$E$: 0.10 vs 0.05'),('matching_pool','random_each_round','Regrouped vs fixed')]
fig=plt.figure(figsize=(183/25.4,135/25.4))
gs=fig.add_gridspec(2,5,left=.245,right=.985,bottom=.10,top=.91,height_ratios=[1.7,1],hspace=.30,wspace=.18)
record_count=0
for j,(r,color) in enumerate(zip(RN,RC)):
    ax=fig.add_subplot(gs[0,j]);bx=fig.add_subplot(gs[1,j])
    ax.axhspan(-.5,4.5,color='#F0F4F6',zorder=0)
    if r==1:ax.set_facecolor('#FCF8F1');bx.set_facecolor('#FCF8F1')
    for y,(block,lev,lab) in enumerate(levels):
        z=A[A.block.eq(block)&A.level.astype(str).eq(lev)&A.R.eq(r)].iloc[0]
        err(ax,np.array([y]),np.array([z['mean']*100]),np.array([z.lo*100]),np.array([z.hi*100]),color,horizontal=True,ms=4.8)
        record_count+=1
    ax.set(xlim=(-6,106),ylim=(11.7,-.7),xticks=[0,50,100],yticks=range(12))
    ax.set_yticklabels([x[2] for x in levels] if j==0 else [],fontsize=8)
    ax.axhline(4.5,color='#8F999E',lw=.65)
    title(ax,string.ascii_lowercase[j],f'$R={r:.2f}$');style(ax,grid='x')
    ax.tick_params(axis='y',length=0)
    ax.set_xlabel('Contribution (%)',fontsize=8)
    for y,(block,lev,lab) in enumerate(rows):
        z=E[E.block.eq(block)&E.level.astype(str).eq(lev)&E.R.eq(r)].iloc[0]
        err(bx,np.array([y]),np.array([z['mean']*100]),np.array([z.lo*100]),np.array([z.hi*100]),color,horizontal=True,ms=4.8)
        record_count+=1
    bx.set(xlim=(-4,4),ylim=(5.6,-.6),xticks=[-4,0,4],yticks=range(6))
    bx.set_yticklabels([x[2] for x in rows] if j==0 else [],fontsize=8)
    style(bx,grid='x');bx.tick_params(axis='y',length=0)
    bx.axvline(0,color='#7B858A',lw=.65)
    title(bx,string.ascii_lowercase[j+5],f'$R={r:.2f}$')
    bx.set_xlabel('Difference (pp)',fontsize=8)
fig.text(.245,.97,'DeepSeek',fontsize=12,fontweight='bold',ha='left')
save(fig,'Figure_S3',record_count,'All 60 absolute estimates and 30 contrasts retain original 95% intervals. Shared scales within each row.')

assert inputs=={f:sha(P/f) for f in files}
manifest={'inputs':inputs,'figures':reports,'backend':'Python / matplotlib',
          'exports':{f.name:sha(f) for f in O.iterdir() if f.is_file()}}
(B/'figure_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')

print(json.dumps(reports,indent=2))
