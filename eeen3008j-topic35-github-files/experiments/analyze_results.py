"""Run-level percentile bootstrap, tuning-only selection, paired evaluation."""
import sys, json, csv, hashlib
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.deps'))
import numpy as np
from scan_v02 import OUT, write_csv

METRICS=['rmse_m','bytes_per_s','over_tolerance_s','over_tolerance_fraction','mean_aoi_s',
         'data_bytes','ack_bytes','max_aoi_s']

def read(path):
    rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
    for r in rows:
        for k in r:
            if k not in ('split','point_id','policy','scenario','slice','case'):
                r[k]=float(r[k])
    return rows

def group(rows,keys):
    out=defaultdict(list)
    for r in rows: out[tuple(r[k] for k in keys)].append(r)
    return out

def choose(rows,budget):
    candidates=[]
    for pid,rr in group(rows,['point_id']).items():
        rate=sum(r['bytes_per_s'] for r in rr)/len(rr)
        if rate<=budget+1e-12:
            candidates.append((sum(r['rmse_m'] for r in rr)/len(rr),rate,pid[0]))
    return min(candidates)[2] if candidates else None

def bootstrap(values,indices):
    v=np.asarray(values,dtype=float)
    samples=v[indices].mean(axis=1)
    lo,hi=np.quantile(samples,[.025,.975])
    return float(v.mean()),float(lo),float(hi)

def main():
    tuning=read(OUT/'tuning_runs.csv')
    selections=[]
    for (jump,loss,policy),rr in group(tuning,['jump','loss','policy']).items():
        for budget in (24,48,96):
            selections.append(dict(jump=jump,loss=loss,policy=policy,budget=budget,
                                   point_id=choose(rr,budget),selection_source='tuning seeds 0..9'))
    # Persist tuning-only choices before reading evaluation results.
    (OUT/'selected_configs.json').write_text(json.dumps(selections,indent=2),encoding='utf-8')
    evaluation=read(OUT/'evaluation_runs.csv')
    rng=np.random.default_rng(20261103)
    indices=rng.integers(0,30,(10000,30))
    def summarize(rr,identity):
        rr=sorted(rr,key=lambda x:x['seed'])
        assert [r['seed'] for r in rr]==list(range(100,130))
        result=dict(**identity,n=30)
        for m in METRICS:
            mean,lo,hi=bootstrap([r[m] for r in rr],indices)
            result.update({m+'_mean':mean,m+'_lo':lo,m+'_hi':hi})
        return result
    groups=group(evaluation,['jump','loss','point_id'])
    summary=[]
    for (j,l,pid),rr in groups.items():
        summary.append(summarize(rr,dict(jump=j,loss=l,point_id=pid,policy=rr[0]['policy'])))
    write_csv(OUT/'workpoint_summary.csv',summary)
    selected=[]; chosen={}
    for s in selections:
        if s['point_id'] is None: continue
        rr=groups[(s['jump'],s['loss'],s['point_id'])]
        chosen[(s['jump'],s['loss'],s['budget'],s['policy'])]=sorted(rr,key=lambda r:r['seed'])
        selected.append(summarize(rr,s)|dict(over_budget_runs=sum(r['bytes_per_s']>s['budget'] for r in rr)))
    write_csv(OUT/'selected_evaluation.csv',selected)
    paired=[]
    for j in (0,.5,1,2):
        for l in (0,.1,.3):
            for b in (24,48,96):
                for comparator in ('error','periodic','age'):
                    ea=chosen.get((j,l,b,'error_age')); other=chosen.get((j,l,b,comparator))
                    if ea is None or other is None: continue
                    row=dict(jump=j,loss=l,budget=b,contrast='EA minus '+comparator,n=30)
                    for m in METRICS:
                        mean,lo,hi=bootstrap([a[m]-o[m] for a,o in zip(ea,other)],indices)
                        row.update({m+'_mean':mean,m+'_lo':lo,m+'_hi':hi})
                    paired.append(row)
    write_csv(OUT/'paired_differences.csv',paired)
    info=dict(bootstrap='percentile; run-level seed resampling; shared resampling indices preserve pairing',
              replicates=10000,seed=20261103,n=30,workpoints=len(summary),selection_count=len(selections),
              infeasible=sum(s['point_id'] is None for s in selections),
              simultaneous_band=False,evaluation_pareto='descriptive, not selection-adjusted',
              source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              numpy=np.__version__)
    (OUT/'statistics_manifest.json').write_text(json.dumps(info,indent=2))
    print(info)

if __name__=='__main__': main()
