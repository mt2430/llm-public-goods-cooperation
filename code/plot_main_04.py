"""Publication figures for action composition, transitions, and group dispersion."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,to_rgba
from matplotlib.patches import Patch
from matplotlib.text import Text
from PIL import Image

import os
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/main_04_actions'
OUT=Path(os.environ.get('PGG_OUTPUT_DIR',str(ROOT/'reproduced')))/'main_04'
OUT.mkdir(parents=True,exist_ok=True)
ORDER=['deepseek_reasoning_enabled', 'kimi_reasoning_enabled', 'claude_reasoning_enabled', 'glm_reasoning_enabled', 'gpt_reasoning_enabled', 'gemini_reasoning_enabled']
C=pd.read_csv(DATA/'state_composition.csv')
S=pd.read_csv(DATA/'state_support.csv')
NAMES={'kimi_reasoning_enabled':'Kimi','deepseek_reasoning_enabled':'DeepSeek',
 'claude_reasoning_enabled':'Claude','glm_reasoning_enabled':'GLM',
 'gpt_reasoning_enabled':'GPT','gemini_reasoning_enabled':'Gemini'}
COMMS=['none','once_public','each_public']
LABEL={'none':'No\ncommunication','once_public':'First-round\npublic','each_public':'Every-round\npublic'}
STATES=['Zero','Partial','Full']
COLORS=['#99A2A7','#83AEC1','#C77A4F']
RS=[.4,.6,.8,.9,.95,.98,1,1.02,1.05,1.1,1.2]
NS=[4,6,8,12]
SEQ=LinearSegmentedColormap.from_list('behavior',['#FBFBF9','#DDE9EE','#A6C4D0','#5E91A8'])
SEQ.set_bad('#EFEFEF')
W=183
plt.rcParams.update({'font.family':'Arial','font.size':8.5,'axes.labelsize':8.5,'axes.titlesize':8.5,
 'xtick.labelsize':8.5,'ytick.labelsize':8.5,'axes.linewidth':.5,'text.color':'black',
 'axes.labelcolor':'black','axes.edgecolor':'black','xtick.color':'black','ytick.color':'black',
 'axes.unicode_minus':True,'mathtext.fontset':'custom','mathtext.rm':'Arial',
 'mathtext.it':'Arial:italic','mathtext.bf':'Arial:bold','svg.fonttype':'none','pdf.fonttype':42,
 'figure.facecolor':'white','savefig.facecolor':'white'})
exports=[]

def axes(fig,H,x,y,w,h):return fig.add_axes([x/W,y/H,w/W,h/H])
def frame(ax):
    for spine in ax.spines.values():spine.set_visible(True);spine.set_color('black')
    ax.tick_params(direction='in',top=False,right=False,length=2,width=.45,pad=1.5)
def groups_label(cfg,kind):
    sub=S[S.configuration_id.eq(cfg)] if kind!='dispersion' else D[D.configuration_id.eq(cfg)]
    low,high=sub.n_groups.min(),sub.n_groups.max()
    return f'$n={int(low)}$' if low==high else f'$n={int(low)}–{int(high)}$'
def heading(fig,H,cfg,x,y,right,kind='state'):
    fig.text(x/W,y/H,NAMES[cfg].replace('†','') if kind=='dispersion' else NAMES[cfg],
             fontsize=11,fontweight='bold',va='baseline')


def save(fig,H,stem,blocks):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();outside=[]
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text().strip():continue
        assert to_rgba(text.get_color())[:3]==(0.,0.,0.)
        b=text.get_window_extent(renderer)
        if b.x0<-.5 or b.y0<-.5 or b.x1>fig.bbox.width+.5 or b.y1>fig.bbox.height+.5:outside.append(text.get_text())
    assert not outside,(stem,outside)
    for text in fig.texts:
        if not text.get_visible() or not text.get_text().strip():continue
        b=text.get_window_extent(renderer)
        for ax in fig.axes:assert not b.overlaps(ax.bbox),(stem,text.get_text())
    for ext in ['pdf','svg']:fig.savefig(OUT/f'{stem}.{ext}')
    fig.savefig(OUT/f'{stem}.png',dpi=600)
    fig.savefig(OUT/f'{stem}_preview.png',dpi=220)
    image=Image.open(OUT/f'{stem}.png')
    sx,sy=image.width/W,image.height/H
    for i,(x0,y0,x1,y1) in enumerate(blocks):
        crop=image.crop((round(x0*sx),round((H-y1)*sy),round(x1*sx),round((H-y0)*sy)))
        crop.resize((1300,round(crop.height*1300/crop.width))).save(OUT/f'{stem}_model_{i+1:02d}.png')
    exports.append({'file':stem,'size_mm':[W,H],'axes_with_colorbar':len(fig.axes),'outside_text':outside,
                    'all_text_black':True,'editable_text':True})
    plt.close(fig)

# F03: three communication conditions, each with equal-R state shares.
H=162
fig=plt.figure(figsize=(W/25.4,H/25.4));blocks=[]
for idx,cfg in enumerate(ORDER):
    row,col=divmod(idx,2);x=12+col*92;y=21+(2-row)*47
    heading(fig,H,cfg,x,y+37,x+78)
    for j,comm in enumerate(COMMS):
        ax=axes(fig,H,x+j*26.8,y,22,30)
        sub=C[C.configuration_id.eq(cfg)&C.communication.eq(comm)]
        mat=sub.pivot(index='round',columns='state',values='share').loc[range(1,11),range(3)]
        ax.stackplot(mat.index,mat.to_numpy().T*100,colors=COLORS,linewidth=0,alpha=1)
        ax.set(xlim=(1,10),ylim=(0,100),xticks=[1,5,10],yticks=[0,50,100])
        ax.tick_params(labelleft=(j==0))
        ax.set_title(LABEL[comm],fontsize=8,pad=3)
        frame(ax)
        if j==0:ax.set_ylabel('Action share (%)',labelpad=2)
    blocks.append((0 if col==0 else 94,y-5,94 if col==0 else W,y+47))
fig.text(.5,12/H,'Round',ha='center',fontsize=8.5)
fig.legend(handles=[Patch(facecolor=c,label=f'{s} contribution') for c,s in zip(COLORS,STATES)],
    loc='lower center',bbox_to_anchor=(.5,2.5/H),ncol=3,frameon=False,fontsize=8.5,
    handlelength=1.4,columnspacing=2,borderpad=0,borderaxespad=0)
save(fig,H,'Figure_4',blocks)
