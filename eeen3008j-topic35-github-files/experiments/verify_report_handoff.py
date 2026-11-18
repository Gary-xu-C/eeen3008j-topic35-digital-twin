"""Stage 3 read-only numerical checks; stdlib only, no simulation or frozen writes."""
from pathlib import Path
import csv,json,hashlib,math
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'results/v0.2';OUT=ROOT/'results/report_v03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def close(a,b):assert math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12),(a,b)
def main():
    frozen=json.loads((SRC/'release_audit.json').read_text())['source_and_output_sha256']
    for name,h in frozen.items():assert sha(ROOT/name)==h,name
    evidence=json.loads((OUT/'evidence_manifest.json').read_text())
    for name,h in evidence['outputs'].items():assert sha(ROOT/name)==h,name
    assert sha(ROOT/'prepare_report_evidence.py')==evidence['generator_sha256']
    groups=defaultdict(list)
    for r in read(SRC/'evaluation_runs.csv'):groups[(float(r['jump']),float(r['loss']),r['point_id'])].append(r)
    for rr in groups.values():
        rr.sort(key=lambda r:int(r['seed']));assert [int(r['seed']) for r in rr]==list(range(100,130))
    original={(float(r['jump']),float(r['loss']),float(r['budget']),r['policy']):r for r in read(SRC/'selected_evaluation.csv')}
    table=read(OUT/'report_selected_results.csv');assert len(table)==144
    metrics=('rmse_m','over_tolerance_s','bytes_per_s','mean_aoi_s')
    feasible=over=0
    for r in table:
        if r['feasible']=='False':
            assert r['rmse_m_mean']=='' and int(r['n'])==0;continue
        feasible+=1
        rr=groups[(float(r['jump']),float(r['loss']),r['point_id'])]
        old=original[(float(r['jump']),float(r['loss']),float(r['budget_B_s']),r['policy'])]
        for m in metrics:
            close(r[m+'_mean'],sum(float(v[m]) for v in rr)/30)
            for k in ('mean','lo','hi'):close(r[m+'_'+k],old[m+'_'+k])
        count=sum(float(v['bytes_per_s'])>float(r['budget_B_s']) for v in rr)
        assert count==int(r['over_budget_runs']);over+=count
        close(float(r['data_rate_B_s_mean'])+float(r['ack_rate_B_s_mean']),r['bytes_per_s_mean'])
    assert feasible==139 and over==34
    ablation=read(OUT/'fixed_eta_ablation.csv');assert len(ablation)==300
    assert len({(r['jump'],r['loss'],r['eta'],r['max_age']) for r in ablation})==300
    for r in ablation:
        e=groups[(float(r['jump']),float(r['loss']),r['E_point'])]
        ea=groups[(float(r['jump']),float(r['loss']),r['EA_point'])]
        for a,b in zip(ea,e):
            close(a['error_threshold'],b['error_threshold']);close(a['error_threshold'],r['eta']);close(a['max_age'],r['max_age'])
        for m in metrics:
            close(r['E_'+m],sum(float(v[m]) for v in e)/30)
            close(r['EA_'+m],sum(float(v[m]) for v in ea)/30)
            close(r['delta_'+m],sum(float(a[m])-float(b[m]) for a,b in zip(ea,e))/30)
            assert float(r['delta_'+m+'_lo'])<=float(r['delta_'+m+'_hi'])
        assert int(r['same_bytes_seeds_exact'])==sum(int(a['total_bytes'])==int(b['total_bytes']) for a,b in zip(ea,e))
        assert int(r['same_rmse_seeds_tol1e12'])==sum(abs(float(a['rmse_m'])-float(b['rmse_m']))<=1e-12 for a,b in zip(ea,e))
    counts=Counter(r['mean_relation'] for r in ablation)
    assert counts=={'RMSE_lower__cost_higher':162,'RMSE_higher__cost_higher':36,'RMSE_same__cost_higher':75,'RMSE_same__cost_same':27}
    result=dict(status='passed',frozen_artifacts_checked=len(frozen),selection_records=144,feasible=139,infeasible=5,
                over_cap_evaluation_uses=34,ablation_contrasts=300,relation_counts=dict(counts),
                new_simulations=0,verification='raw means/pairing/counts recomputed; selected intervals matched to frozen outputs; not an independent full CI recomputation')
    (OUT/'handoff_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
