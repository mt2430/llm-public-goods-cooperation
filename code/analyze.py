"""Audit the numerical record; optionally rerun Figure 6's original bootstrap."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'reanalysis')
    parser.add_argument('--rebuild-size-bootstrap',action='store_true',help='Recompute all Figure 6 estimates and 10,000-resample intervals.')
    args=parser.parse_args();out=args.output.resolve()
    for protected in [ROOT/'data',ROOT/'figures',ROOT/'code']:
        if out==protected or protected in out.parents or out in protected.parents:
            parser.error('Use an output folder separate from the frozen inputs and approved figures.')
    out.mkdir(parents=True,exist_ok=True)
    report=[]
    def check(label,a,b,atol=2e-12):
        a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
        assert a.shape==b.shape,(label,a.shape,b.shape)
        maximum=float(np.nanmax(np.abs(a-b))) if a.size else 0.
        assert np.allclose(a,b,atol=atol,rtol=0,equal_nan=True),(label,maximum)
        report.append({'check':label,'values':int(a.size),'maximum_absolute_difference':maximum,'passed':True})

    g=pd.read_csv(DATA/'group_records/no_communication_trajectories.csv')
    q=pd.read_csv(DATA/'group_records/no_communication_rounds.csv')
    assert not q.duplicated(['trajectory_id','round']).any()
    z=q.groupby('trajectory_id').contribution_rate.mean()
    check('No-communication group means from 80,150 observed rounds',z,g.set_index('trajectory_id').loc[z.index,'atlas_mean'])
    means=g.groupby('atlas_cell_id').atlas_mean.mean()
    counts=g.groupby('atlas_cell_id').size()
    for label,path in [('Figures 1 and 2','main_01_02/condition_statistics_N6.csv'),('Figure 7','main_06_07/Figure_7_conditions.csv')]:
        c=pd.read_csv(DATA/path).set_index('atlas_cell_id')
        check(label+' condition means',means.loc[c.index],c['mean'])
        check(label+' group counts',counts.loc[c.index],c.n,atol=0)

    cg=pd.read_csv(DATA/'main_03_communication/trajectory_source_data.csv')
    cq=pd.read_csv(DATA/'main_03_communication/complete_rounds.csv')
    z=cq.groupby('trajectory_id').contribution_rate.mean()
    check('Communication group means from all 24,100 rounds',z,cg.set_index('trajectory_id').loc[z.index,'atlas_mean'])
    cm=cg.groupby(['configuration_id','R','communication']).atlas_mean.mean()
    effects=pd.read_csv(DATA/'main_03_communication/effects_by_R.csv')
    expected=[];observed=[]
    for row in effects[effects.metric.eq('whole_run')].itertuples():
        expected.append((cm.loc[(row.configuration_id,row.R,row.arm_a)]-cm.loc[(row.configuration_id,row.R,row.arm_b)])*100)
        observed.append(row.estimate_pp)
    check('Figure 3 whole-run communication differences in percentage points',expected,observed)

    actions=pd.read_csv(DATA/'main_04_actions/individual_action_source.csv')
    # Reconstruct each R-specific distribution first, then average the three R values equally.
    keys=['configuration_id','communication','R','round']
    sizes=actions.groupby(keys).size()
    frequencies=actions.groupby(keys+['state']).size().unstack('state',fill_value=0).reindex(columns=[0,1,2],fill_value=0)
    shares=frequencies.div(sizes,axis=0).groupby(level=['configuration_id','communication','round']).mean().stack()
    shares.index=shares.index.set_names(['configuration_id','communication','round','state'])
    recorded=pd.read_csv(DATA/'main_04_actions/state_composition.csv').set_index(['configuration_id','communication','round','state'])
    check('Figure 4 all 540 action shares from 86,820 individual actions',shares.loc[recorded.index],recorded.share)

    tg=pd.read_csv(DATA/'main_05_termination/termination_trajectory_means.csv')
    tq=pd.read_csv(DATA/'main_05_termination/random_round_source.csv')
    z=tq.groupby('slot_id').contribution_rate.mean()
    check('Figure 5 random-duration means from 4,668 observed rounds',z,tg[tg.regime.eq('random')].set_index('trajectory_id').loc[z.index,'mean'])
    ts=pd.read_csv(DATA/'main_05_termination/termination_summary.csv')
    groupmean=tg.groupby(['model','R','regime'])['mean'].mean()
    zz=ts[ts.metric.eq('whole_run')].set_index(['model','R','regime'])
    check('Figure 5 equal-group weighted summaries',groupmean.loc[zz.index],zz['mean'])

    st=pd.read_csv(DATA/'main_06_07/Figure_6_trajectories.csv')
    sm=pd.read_csv(DATA/'main_06_07/Figure_6_summary.csv')
    metrics=['mean','late','final']
    point=st.groupby(['configuration_id','communication','N','R'])[metrics].mean().groupby(level=[0,1,2]).mean()*100
    exact=[];published=[]
    for r in sm.itertuples():
        exact.append(point.loc[(r.configuration_id,r.communication,r.N),r.metric]);published.append(r.estimate)
    check('Figure 6 equal-R weighted outcome summaries',exact,published)

    sg=pd.read_csv(DATA/'supplementary/S2_group_outcomes_R090.csv')
    merged=sg.merge(cg[['trajectory_id','atlas_mean']],on='trajectory_id',suffixes=('_si','_main'),validate='one_to_one')
    assert len(merged)==len(sg)==483
    check('Figure S2 group outcomes agree with the communication cohorts',merged.atlas_mean_si,merged.atlas_mean_main)

    if args.rebuild_size_bootstrap:
        boot={};points={};rows=[]
        for key,z in st.groupby(['configuration_id','communication','N','R'],sort=True):
            v=z[metrics].to_numpy();n=len(v)
            seed=int.from_bytes(hashlib.sha256(('main_size|'+str(key)).encode()).digest()[:8],'little')
            rng=np.random.default_rng(seed)
            boot[key]=rng.multinomial(n,np.full(n,1/n),size=10000)@v/n
            points[key]=v.mean(axis=0)
        for key,z in st.groupby(['configuration_id','communication','N'],sort=True):
            draws=np.mean([boot[(*key,r)] for r in [.6,.9,.98]],axis=0)
            center=np.mean([points[(*key,r)] for r in [.6,.9,.98]],axis=0)
            for j,m in enumerate(metrics):
                lo,hi=np.quantile(draws[:,j],[.025,.975])*100
                rows.append(dict(configuration_id=key[0],communication=key[1],N=key[2],metric=m,estimate=center[j]*100,lo=lo,hi=hi,n=len(z)))
        rebuilt=pd.DataFrame(rows)
        rebuilt.to_csv(out/'Figure_6_summary_recomputed.csv',index=False,encoding='utf-8-sig')
        keys=['configuration_id','communication','N','metric']
        a=rebuilt.set_index(keys).sort_index();b=sm.set_index(keys).sort_index()
        check('Figure 6 original 10,000-resample estimates and confidence intervals',a[['estimate','lo','hi']],b[['estimate','lo','hi']],atol=3e-11)
    (out/'numerical_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
