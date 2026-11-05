from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.colors import to_rgba
import os
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/main_01_02'
OUT=Path(os.environ.get('PGG_OUTPUT_DIR',str(ROOT/'reproduced')))/'main_01_02'
OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 9,
    'axes.labelsize': 9, 'axes.titlesize': 9.5,
    'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5,
    'axes.linewidth': 0.65, 'axes.edgecolor': 'black',
    'text.color': 'black', 'axes.labelcolor': 'black',
    'xtick.color': 'black', 'ytick.color': 'black',
    'legend.frameon': False, 'svg.fonttype': 'none', 'pdf.fonttype': 42,
    'mathtext.fontset': 'custom', 'mathtext.rm': 'Arial',
    'mathtext.it': 'Arial:italic', 'mathtext.bf': 'Arial:bold',
    'figure.facecolor': 'white', 'savefig.facecolor': 'white',
})


audit=[]
def axmm(fig, x, y, w, h):
    width, height = fig.get_size_inches() * 25.4
    return fig.add_axes([x / width, y / height, w / width, h / height])

def style(ax, grid=True):
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor('black')
    ax.tick_params(direction='in', top=False, right=False, length=3, width=.65, pad=3)
    if grid:
        ax.grid(axis='y', color='#E6E8EA', lw=.4)
    ax.set_axisbelow(True)

def curve(ax, x, y, lo, hi, color, marker='o', size=4.8, z=3):
    x, y, lo, hi = map(np.asarray, (x, y, lo, hi))
    assert np.all(lo <= y + 1e-8) and np.all(hi >= y - 1e-8)
    ax.fill_between(x, lo, hi, color=color, alpha=.13, lw=0, zorder=z-1)
    ax.plot(x, y, color=color, lw=.85, ls=(0, (2.5, 2.0)), zorder=z)
    ax.plot(x, y, linestyle='none', marker=marker, color=color,
            ms=size, mec='white', mew=.45, zorder=z+.1)

def save(fig, stem):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    outside, tick_collisions = [], []
    for t in fig.findobj(Text):
        if t.get_visible() and t.get_text():
            b = t.get_window_extent(renderer)
            if b.x0 < -.5 or b.y0 < -.5 or b.x1 > fig.bbox.x1+.5 or b.y1 > fig.bbox.y1+.5:
                outside.append(t.get_text())
    for ax in fig.axes:
        ticks = [t for t in ax.get_xticklabels() if t.get_visible()]
        for a, b in zip(ticks, ticks[1:]):
            if a.get_window_extent(renderer).overlaps(b.get_window_extent(renderer)):
                tick_collisions.append([a.get_text(), b.get_text()])
        for spine in ax.spines.values():
            assert spine.get_visible() and to_rgba(spine.get_edgecolor()) == to_rgba('black')
        for axis in [ax.xaxis, ax.yaxis]:
            for tick in axis.get_major_ticks():
                assert tick._tickdir == 'in' and not tick.tick2line.get_visible()
    assert not outside, outside
    assert not tick_collisions, tick_collisions
    for ext in ['pdf', 'svg']:
        fig.savefig(OUT / (stem + '.' + ext))
    fig.savefig(OUT / (stem + '.png'), dpi=600)
    fig.savefig(OUT / (stem + '_preview.png'), dpi=220)
    audit.append({'figure': stem, 'size_mm': (fig.get_size_inches()*25.4).tolist(),
                  'panels': len(fig.axes), 'outside_text': outside,
                  'overlapping_adjacent_ticks': tick_collisions})
    plt.close(fig)
names=dict(zip(['deepseek_reasoning_enabled','kimi_reasoning_enabled','claude_reasoning_enabled','glm_reasoning_enabled','gpt_reasoning_enabled','gemini_reasoning_enabled'],['DeepSeek','Kimi','Claude','GLM','GPT','Gemini']))
palette=dict(zip(names,['#327C9E','#866395','#BB788E','#59666B','#CC794D','#35967F']))

c=pd.read_csv(DATA/'condition_statistics_N6.csv')
q=pd.read_csv(DATA/'round_statistics_N6.csv')
order=c[c.R.lt(1)].groupby('configuration_id')['mean'].mean().sort_values(kind='stable').index.tolist()

rs=[.4,.9,.98,1.1];cols={.4:'#367E9D',.9:'#CB794D',.98:'#866395',1.1:'#929DA2'}
fig=plt.figure(figsize=(183/25.4,110/25.4))
fig.text(178/183,106/110,'No communication; $N=6$, $T=10$',ha='right',va='top',fontsize=8.5)
for i,cfg in enumerate(order):
 ax=axmm(fig,15+(i%3)*56,65 if i<3 else 18,49,32)
 for r in rs:
  z=q[q.configuration_id.eq(cfg)&q.R.eq(r)].sort_values('round')
  assert len(z)==10
  curve(ax,z['round'],z['mean']*100,z.lo*100,z.hi*100,cols[r],marker='s' if r>1 else 'o',size=4.4)
 ax.set(xlim=(.7,10.3),ylim=(-5,105),xticks=[1,5,10],yticks=[0,50,100]);style(ax)
 ax.set_title(f'{chr(97+i)}  {names[cfg]}',loc='left',fontsize=10,fontweight='bold',pad=5)
 if i%3==0:ax.set_ylabel('Contribution (%)')
 if i>=3:ax.set_xlabel('Round $t$')
 if i==0:
  handles=[Line2D([],[],color=cols[r],marker='s' if r>1 else 'o',ms=4.4,lw=.8,ls='--') for r in rs]
  ax.legend(handles,[f'$R={r:.2f}$' for r in rs],loc='center right',fontsize=8,handlelength=1.5,labelspacing=.25)
save(fig,'Figure_1')
fig=plt.figure(figsize=(183/25.4,79/25.4))
for i,metric in enumerate(['mean','final','mean']):
    ax=axmm(fig,14+i*59,18,48,51)
    for cfg in order:
        z=c[c.configuration_id.eq(cfg)&(c.R.lt(1) if i==2 else True)].sort_values('R')
        curve(ax,z.R,z[metric]*100,z[metric+'_lo']*100,z[metric+'_hi']*100,palette[cfg],size=4.5)
    ax.set(ylim=(-5,105),yticks=[0,50,100],xlabel='Normalized synergy $R$')
    if i==2:ax.set(xlim=(.38,1),xticks=[.4,.6,.8,.98],xticklabels=['0.40','0.60','0.80','0.98'])
    else:
        ax.set(xlim=(.38,1.22),xticks=[.4,.8,1,1.2],xticklabels=['0.4','0.8','1.0','1.2'])
        ax.axvline(1,color='#555555',lw=.6,ls='--',zorder=0)
    if i==0:ax.set_ylabel('Contribution (%)')
    ax.set_title(chr(97+i),loc='left',fontsize=11,fontweight='bold',pad=5)
    style(ax)
    if i==1:
        handles=[Line2D([],[],color=palette[cfg],marker='o',ms=4.5,lw=.8,ls='--') for cfg in order]
        ax.legend(handles,[names[cfg] for cfg in order],loc='center left',fontsize=8.5,handlelength=1.1,labelspacing=.35)
save(fig,'Figure_2')


(OUT/'plot_checks.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
