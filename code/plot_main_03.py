"""Six model blocks combining communication dynamics and statistical differences."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgba
from matplotlib.text import Text
from PIL import Image

import os
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/main_03_communication'
OUT=Path(os.environ.get('PGG_OUTPUT_DIR',str(ROOT/'reproduced')))/'main_03'
OUT.mkdir(parents=True,exist_ok=True)
WIDTH, HEIGHT = 183, 177
AXSIZE = 7.2
BLOCK_X = [14.0, 106.0]
BLOCK_WIDTH = 74.0
ROW_STEP = 54
CURVE_WIDTH, CURVE_HEIGHT = 24.5, 15
CURVE_DX, CURVE_DY = 29, 22
FULL_HEIGHT = CURVE_DY + CURVE_HEIGHT
NAMES = {'kimi_reasoning_enabled': 'Kimi',
    'deepseek_reasoning_enabled': 'DeepSeek',
    'claude_reasoning_enabled': 'Claude',
    'glm_reasoning_enabled': 'GLM',
    'gpt_reasoning_enabled': 'GPT',
    'gemini_reasoning_enabled': 'Gemini'}
ARMS = ['none', 'once_public', 'each_public']
ARM_COLOR = {'none': '#99A2A7', 'once_public': '#397A9A', 'each_public': '#C77A4F'}
ARM_MARKER = {'none': 'o', 'once_public': 'o', 'each_public': 's'}
ARM_LABEL = {'none': 'No communication', 'once_public': 'First-round public', 'each_public': 'Every-round public'}
CONTRASTS = ['first_minus_none', 'every_minus_none', 'every_minus_first']
CONTRAST_COLOR = {'first_minus_none': '#397A9A', 'every_minus_none': '#C77A4F', 'every_minus_first': '#59666C'}
CONTRAST_MARKER = {'first_minus_none': 'o', 'every_minus_none': 's', 'every_minus_first': '^'}
CONTRAST_LABEL = {'first_minus_none': 'First − none', 'every_minus_none': 'Every − none', 'every_minus_first': 'Every − first'}
SELECTED_R = [.60, .98, 1., 1.02]
ALL_R = [.60, .90, .98, 1., 1.02]
METRICS = ['whole_run', 'late_stage', 'final_round']
CMAP = LinearSegmentedColormap.from_list('difference', ['#3B6F93', '#C8DCE5', '#FAF9F6', '#E5C5AA', '#B76E3D'])
NORM = Normalize(-100, 100)

plt.rcParams.update({'font.family': 'Arial', 'font.size': AXSIZE,
    'axes.labelsize': AXSIZE, 'axes.titlesize': AXSIZE, 'xtick.labelsize': AXSIZE,
    'ytick.labelsize': AXSIZE, 'axes.linewidth': .5, 'text.color': 'black',
    'axes.labelcolor': 'black', 'axes.edgecolor': 'black', 'xtick.color': 'black',
    'ytick.color': 'black', 'axes.unicode_minus': True,
    'mathtext.fontset': 'custom', 'mathtext.rm': 'Arial', 'mathtext.it': 'Arial:italic',
    'mathtext.bf': 'Arial:bold', 'svg.fonttype': 'none', 'pdf.fonttype': 42,
    'figure.facecolor': 'white', 'savefig.facecolor': 'white'})

ORDER=['deepseek_reasoning_enabled', 'kimi_reasoning_enabled', 'claude_reasoning_enabled', 'glm_reasoning_enabled', 'gpt_reasoning_enabled', 'gemini_reasoning_enabled']
manifest={}
ROUND = pd.read_csv(DATA / 'round_source_data.csv')
EFFECT = pd.read_csv(DATA / 'effects_by_R.csv')
POOLED = pd.read_csv(DATA / 'social_dilemma_effects.csv')
CELLS = pd.read_csv(DATA / 'derived_condition_metrics.csv')
SIZES = pd.read_csv(DATA / 'model_sample_summary.csv').set_index('configuration_id')
assert len(ROUND) == 900 and len(EFFECT) == 270 and len(POOLED) == 54
assert set(ROUND.configuration_id) == set(ORDER) == set(EFFECT.configuration_id)
assert not ROUND.configuration_id.str.contains('disabled|_none').any()
assert SIZES.groups.sum() == 2410
# Independently reconcile each whole-run heatmap point with its two arm means.
for d in EFFECT[EFFECT.metric.eq('whole_run')].itertuples():
    selected = CELLS[CELLS.configuration_id.eq(d.configuration_id) & np.isclose(CELLS.R, d.R)].set_index('communication')
    expected = (selected.loc[d.arm_a, 'mean'] - selected.loc[d.arm_b, 'mean']) * 100
    assert abs(expected - d.estimate_pp) < 1e-10

def add_axes(fig, x, y, w, h):
    return fig.add_axes([x / WIDTH, y / HEIGHT, w / WIDTH, h / HEIGHT])

def frame(ax):
    ax.tick_params(direction='in', length=1.8, width=.45, pad=1.4, top=False, right=False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color('black')

def panel_title(ax, text):
    ax.set_title(text, fontsize=7.3, loc='left', color='black', pad=2.7)

curve_rows, heat_rows, statistic_rows = [], [], []
fig = plt.figure(figsize=(WIDTH / 25.4, HEIGHT / 25.4))
axes_info = []
for idx, cfg in enumerate(ORDER):
    outer_row, outer_col = divmod(idx, 2)
    x = BLOCK_X[outer_col]
    y = 22 + (2 - outer_row) * ROW_STEP
    fig.text(x / WIDTH, (y + 42.7) / HEIGHT, NAMES[cfg],
             fontsize=9, fontweight='bold', rotation=0, ha='left', va='baseline')
    for j, r in enumerate(SELECTED_R):
        local_row, local_col = divmod(j, 2)
        ax = add_axes(fig, x + local_col * CURVE_DX, y + (1 - local_row) * CURVE_DY, CURVE_WIDTH, CURVE_HEIGHT)
        for comm in ARMS:
            data = ROUND[ROUND.configuration_id.eq(cfg) & np.isclose(ROUND.R, r) & ROUND.communication.eq(comm)].sort_values('round')
            assert len(data) == 10
            ax.fill_between(data['round'].to_numpy(), data.lo.to_numpy() * 100, data.hi.to_numpy() * 100,
                color=ARM_COLOR[comm], alpha=.15, lw=0, zorder=1)
            ax.plot(data['round'], data['mean'] * 100, color=ARM_COLOR[comm], ls=(0, (2, 2)), lw=.4,
                marker=ARM_MARKER[comm], markersize=3.6, markeredgewidth=.25, markeredgecolor='white', zorder=3)
            curve_rows.extend(data.assign(figure_model_index=idx + 1, panel=chr(97 + j)).to_dict('records'))
        ax.set(xlim=(.5, 10.5), ylim=(-6, 106), xticks=[1, 5, 10], yticks=[0, 50, 100])
        ax.tick_params(labelleft=(local_col == 0))
        frame(ax)
        ax.set_axisbelow(True)
        ax.grid(axis='y', color='#E9E9E9', lw=.3)
        panel_title(ax, f'{chr(97 + j)}  $R={r:.2f}$')
        axes_info.append({'model': cfg, 'panel': chr(97 + j), 'role': 'time_course', 'R': r, 'axis': ax})
    fig.text((x - 7.3) / WIDTH, (y + FULL_HEIGHT / 2) / HEIGHT, 'Contribution (%)', rotation=90,
             fontsize=AXSIZE, ha='center', va='center')
    fig.text((x + (CURVE_DX + CURVE_WIDTH) / 2) / WIDTH, (y - 6.5) / HEIGHT, 'Round', fontsize=AXSIZE, ha='center', va='baseline')

    # R is categorical here; cell color and labels show the primary whole-run metric.
    ax = add_axes(fig, x + 64, y, 10, FULL_HEIGHT)
    matrix = np.empty((5, 2))
    for i, r in enumerate(ALL_R):
        for k, name in enumerate(CONTRASTS[:2]):
            d = EFFECT[EFFECT.configuration_id.eq(cfg) & np.isclose(EFFECT.R, r) & EFFECT.contrast.eq(name) & EFFECT.metric.eq('whole_run')].iloc[0]
            matrix[i, k] = d.estimate_pp
            heat_rows.append({**d.to_dict(), 'figure_model_index': idx + 1, 'panel': 'e', 'heatmap_row': i, 'heatmap_column': k})
    im = ax.imshow(matrix, cmap=CMAP, norm=NORM, origin='upper', aspect='auto', interpolation='nearest')
    ax.set_xticks([0, 1], ['First', 'Every'], rotation=90)
    ax.set_yticks(range(5), [f'{r:.2f}' for r in ALL_R])
    ax.set_ylabel('$R$', rotation=0, labelpad=0)
    ax.yaxis.set_label_coords(-.35, 1.02)
    ax.yaxis.label.set_verticalalignment('bottom')
    ax.tick_params(axis='x', pad=2.5)
    frame(ax)
    ax.tick_params(length=0)
    for a in range(5):
        for b in range(2):
            value = int(np.rint(matrix[a, b]))
            ax.text(b, a, str(value), fontsize=7.2, color='black', ha='center', va='center')
    ax.set_xticks(np.arange(-.5, 2, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
    ax.grid(which='minor', color='white', lw=.6)
    ax.tick_params(which='minor', length=0)
    panel_title(ax, 'e  CE (pp)')
    axes_info.append({'model': cfg, 'panel': 'e', 'role': 'whole_run_direct_effect_map', 'axis': ax})

curve_handles = [Line2D([], [], color=ARM_COLOR[c], marker=ARM_MARKER[c], markersize=3.8,
    markeredgecolor='white', markeredgewidth=.25, ls=(0, (2, 2)), lw=.4, label=ARM_LABEL[c]) for c in ARMS]
curve_legend = fig.legend(handles=curve_handles, loc='lower center', bbox_to_anchor=(.5, 10.8 / HEIGHT), ncol=3,
    frameon=False, fontsize=7.6, handlelength=1.5, handletextpad=.5, columnspacing=1.6, borderpad=0, borderaxespad=0)
legend_tags = [fig.text(9.2 / WIDTH, 12.2 / HEIGHT, 'a–d:', fontsize=7.6, ha='left', va='center')]
cax = add_axes(fig, 48, 3, 87, 1.8)
cb = fig.colorbar(im, cax=cax, orientation='horizontal', ticks=[-100, -50, 0, 50, 100])
cb.ax.tick_params(direction='in', length=1.8, width=.45, pad=1.2, labelsize=7)
cb.outline.set_linewidth(.45)
cb.outline.set_edgecolor('black')
legend_tags.append(fig.text(9.2 / WIDTH, 3.9 / HEIGHT, 'e:', fontsize=7.6, ha='left', va='center'))
fig.text(45 / WIDTH, 3.9 / HEIGHT, 'Communication effect (pp)', fontsize=7.2, ha='right', va='center')

# Source exports contain exactly the values represented in the six model blocks.
assert len(curve_rows) == 720 and len(statistic_rows) == 0 and len(heat_rows) == 60
for name, rows in [('plotted_time_courses.csv', curve_rows), ('plotted_direct_effect_map.csv', heat_rows)]:
    pd.DataFrame(rows).to_csv(OUT / name, index=False, encoding='utf-8-sig')

fig.canvas.draw()
renderer = fig.canvas.get_renderer()
for item in [curve_legend]:
    bb = item.get_window_extent(renderer)
    assert abs((bb.x0 + bb.x1) / 2 - fig.bbox.width / 2) < .1
assert abs((cax.bbox.x0 + cax.bbox.x1) / 2 - fig.bbox.width / 2) < .1
assert np.ptp([t.get_window_extent(renderer).x0 for t in legend_tags]) < .1
outside = []
for text in fig.findobj(Text):
    if text.get_visible() and text.get_text().strip():
        assert to_rgba(text.get_color())[:3] == (0., 0., 0.)
        bb = text.get_window_extent(renderer)
        if bb.x0 < -.5 or bb.y0 < -.5 or bb.x1 > fig.bbox.width + .5 or bb.y1 > fig.bbox.height + .5:
            outside.append(text.get_text())
assert not outside, outside
assert len(axes_info) == 30 and len(fig.axes) == 31
for text in fig.texts:
    if text.get_visible() and text.get_text().strip():
        bounds = text.get_window_extent(renderer)
        for record in axes_info:
            assert not bounds.overlaps(record['axis'].bbox), ('outer text overlaps panel', text.get_text(), record['model'], record['panel'])
for i, record in enumerate(axes_info):
    ax = record['axis']
    for other in axes_info[i + 1:]:
        assert not ax.bbox.overlaps(other['axis'].bbox)
    assert all(s.get_visible() for s in ax.spines.values())
for i in range(6):
    block = axes_info[i * 5:i * 5 + 5]
    left = [d['axis'] for d in block[:4]]
    span = [min(a.get_position().y0 for a in left), max(a.get_position().y1 for a in left)]
    for record in block[4:]:
        pos = record['axis'].get_position()
        assert np.allclose([pos.y0, pos.y1], span, atol=1e-12)

stem = 'Figure_3'
fig.savefig(OUT / f'{stem}.pdf')
fig.savefig(OUT / f'{stem}.svg')
fig.savefig(OUT / f'{stem}.png', dpi=600)
fig.savefig(OUT / f'{stem}_preview.png', dpi=240)
image = Image.open(OUT / f'{stem}.png')
sx, sy = image.width / WIDTH, image.height / HEIGHT
for idx, cfg in enumerate(ORDER):
    row, col = divmod(idx, 2)
    y = 22 + (2 - row) * ROW_STEP
    x0, x1 = (0, 90) if col == 0 else (90, 183)
    top, bottom = HEIGHT - (y + 46.5), HEIGHT - (y - 8)
    bounds = (round(x0 * sx), round(top * sy), round(x1 * sx), round(bottom * sy))
    crop = image.crop(bounds)
    crop.resize((1400, round(crop.height * 1400 / crop.width))).save(OUT / f'model_{idx + 1:02d}_detail.png')
plt.close(fig)
