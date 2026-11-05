"""Offline replay of the current seven main and three supplementary figures."""
from pathlib import Path
import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
GROUPS = [
    ('plot_main_01_02.py', ['1', '2']),
    ('plot_main_03.py', ['3']),
    ('plot_main_04.py', ['4']),
    ('plot_main_05.py', ['5']),
    ('plot_main_06_07.py', ['6', '7']),
    ('plot_supplementary.py', ['S1', 'S2', 'S3']),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figures', default='all', help='all or comma-separated: 1,2,3,4,5,6,7,S1,S2,S3')
    parser.add_argument('--output', type=Path, default=ROOT/'reproduced')
    args = parser.parse_args()
    choices = {n for _, ns in GROUPS for n in ns}
    chosen = choices if args.figures.lower() == 'all' else {n.strip().upper() for n in args.figures.split(',')}
    if not chosen or not chosen <= choices:
        parser.error('Unknown figure IDs: '+', '.join(sorted(chosen-choices)))
    out = args.output.resolve()
    # Approved figures and input tables are read-only targets for replay purposes.
    for protected in [ROOT/'figures', ROOT/'data', ROOT/'code']:
        if out == protected or protected in out.parents or out in protected.parents:
            parser.error('Output must be separate from approved figures, data, code.')
    out.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['PGG_OUTPUT_DIR'] = str(out)
    env['MPLBACKEND'] = 'Agg'
    report = {'python':sys.version,'platform':sys.platform,'output':str(out),'selected_figures':sorted(chosen),'jobs':[]}
    report['packages'] = {p:importlib.metadata.version(p) for p in ['numpy','pandas','matplotlib','Pillow']}
    started = time.time()
    for script, ids in GROUPS:
        if not chosen.intersection(ids):
            continue
        tick = time.time()
        print('Rendering '+', '.join(ids)+' ...', flush=True)
        job = subprocess.run([sys.executable,'-E','-X','utf8',str(ROOT/'code'/script)],
                             cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8')
        (out/(script+'.log')).write_text(job.stdout+'\n'+job.stderr,encoding='utf8')
        report['jobs'].append({'script':script,'figures':ids,'returncode':job.returncode,'seconds':round(time.time()-tick,2)})
        if job.returncode:
            (out/'reproduction_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
            print(job.stderr, file=sys.stderr)
            raise SystemExit(job.returncode)
    exports = []
    for figure_id in sorted(chosen):
        stem = 'Figure_'+figure_id
        category = 'supplementary' if figure_id.startswith('S') else 'main'
        for ext in ['pdf','svg','png']:
            candidates = list(out.glob('*/'+stem+'.'+ext))
            assert len(candidates) == 1, (stem,ext,candidates)
            dst = out/'figures'/category/(stem+'.'+ext)
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(candidates[0],dst)
            exports.append(dst.relative_to(out).as_posix())
    report['exports'] = exports
    report['seconds'] = round(time.time()-started,2)
    report['success'] = True
    (out/'reproduction_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('Finished. Output: '+str(out/'figures'),flush=True)


if __name__ == '__main__':
    main()
