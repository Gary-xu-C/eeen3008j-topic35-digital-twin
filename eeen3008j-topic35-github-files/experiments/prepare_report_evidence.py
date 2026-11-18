"""Stage 3: read-only frozen v0.2 input, report tables and fixed-eta ablation.
No simulations and no writes to results/v0.2 or the original release manifest.
"""
import sys,json,csv,hashlib
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.deps'))
import numpy as np
from analyze_results import read,group,bootstrap
from scan_v02 import write_csv
OUT=ROOT/'results/report_v03';SRC=ROOT/'results/v0.2'
FIELDS=('rmse_m','over_tolerance_s','bytes_per_s','mean_aoi_s')
LABEL={'periodic':'P','age':'A','error':'E','error_age':'EA'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    frozen=json.loads((SRC/'release_audit.json').read_text())['source_and_output_sha256']
    assert all(sha(ROOT/p)==h for p,h in frozen.items()),'Frozen release changed'
    rows=read(SRC/'evaluation_runs.csv')
    bypoint=group(rows,['jump','loss','point_id'])
    for rr in bypoint.values():rr.sort(key=lambda r:r['seed'])
    indices=np.random.default_rng(20261103).integers(0,30,(10000,30))
    selections=json.loads((SRC/'selected_configs.json').read_text())
    table=[]
    for s in selections:
        out=dict(jump=s['jump'],loss=s['loss'],budget_B_s=s['budget'],policy=s['policy'],
                 point_id=s['point_id'] or '',feasible=s['point_id'] is not None,n=30 if s['point_id'] else 0,
                 seed_range='100..129' if s['point_id'] else '',over_budget_runs='',source_csv='results/v0.2/evaluation_runs.csv')
        for m in FIELDS+('data_rate_B_s','ack_rate_B_s'):
            for k in ('mean','lo','hi'):out[m+'_'+k]=''
        if s['point_id']:
            rr=bypoint[(s['jump'],s['loss'],s['point_id'])]
            assert [r['seed'] for r in rr]==list(range(100,130))
            out['over_budget_runs']=sum(r['bytes_per_s']>s['budget'] for r in rr)
            for m in FIELDS+('data_rate_B_s','ack_rate_B_s'):
                values=[r['data_bytes' if m=='data_rate_B_s' else 'ack_bytes']/60 for r in rr] if m.endswith('_B_s') else [r[m] for r in rr]
                mean,lo,hi=bootstrap(values,indices)
                out.update({m+'_mean':mean,m+'_lo':lo,m+'_hi':hi})
        table.append(out)
    write_csv(OUT/'report_selected_results.csv',table)
    md=['# Report result tables (v0.2 data; stage 3 extraction)',
        '', 'Frozen inputs only; no new simulations. n=30 paired evaluation seeds (100–129) per feasible candidate. '
        'Configurations were selected using tuning seeds 0–9. Four metrics are run-level means with pointwise 95% percentile bootstrap CI '
        '(10000 resamples, seed 20261103). These are not simultaneous bands or hard-budget comparisons.',
        '', '## Representative frozen candidates', '', '|Policy / configuration|RMSE (m), mean [95% CI]|Time above 0.5 m (s), mean [95% CI]|Total rate (B/s), mean [95% CI]|Mean AoI (s), mean [95% CI]|Over budget|',
        '|---|---|---|---|---|---|']
    def cell(r,m):return '%.5f [%.5f, %.5f]'%(r[m+'_mean'],r[m+'_lo'],r[m+'_hi'])
    for r in table:
        if r['jump']==2 and r['loss']==.1 and r['budget_B_s']==48:
            md.append('|'+LABEL[r['policy']]+' / '+r['point_id']+'|'+'|'.join(cell(r,m) for m in FIELDS)+'|'+str(r['over_budget_runs'])+'/30|')
    md+=['','Condition: |delta v|=2 m/s, loss=0.1, tuning cap=48 B/s. Data and ACK rates are separately available in the machine-readable table.',
         '', '## All 12 conditions at the predeclared 48 B/s tuning cap', '',
         'Each cell is **RMSE (m); actual total B/s; over-cap runs/30**. Full four-metric intervals and all budgets are in `results/report_v03/report_selected_results.csv`. '
         'This cap does not equalize actual consumption. Zero-motion repetitions check the pipeline, rather than establish a stochastic zero-error discovery. '
         'Frozen zero-motion candidates may differ because of roundoff-scale RMSE ordering; those negligible differences do not establish a physical accuracy ranking.', '',
         '|Jump magnitude (m/s)|Loss|P|A|E|EA|','|---|---|---|---|---|---|']
    for j in (0,.5,1,2):
        for loss in (0,.1,.3):
            rr=[r for r in table if r['jump']==j and r['loss']==loss and r['budget_B_s']==48]
            cells=[]
            for policy in ('periodic','age','error','error_age'):
                r=next(r for r in rr if r['policy']==policy)
                cells.append('%.5f; %.3f; %d/30'%(r['rmse_m_mean'],r['bytes_per_s_mean'],r['over_budget_runs']) if r['feasible'] else 'No feasible tuning point')
            md.append('|%g|%g|'%(j,loss)+'|'.join(cells)+'|')
    md+=['','## Budget feasibility across all conditions', '', '|Tuning cap (B/s)|Feasible selections / 48|Infeasible|Over-cap evaluation uses / feasible uses|', '|---|---|---|---|']
    for b in (24,48,96):
        rr=[r for r in table if r['budget_B_s']==b];feasible=[r for r in rr if r['feasible']]
        md.append('|%d|%d/48|%d|%d/%d|'%(b,len(feasible),48-len(feasible),sum(r['over_budget_runs'] for r in feasible),30*len(feasible)))
    md+=['', 'An evaluation run may appear at multiple budgets; the final column counts uses, not independent trajectories. '
         'No feasible point means no point in the predeclared grid met the **mean tuning** cap; it is not a physical impossibility theorem.', '',
         '## Exact lookup', '', 'For each table record, filter evaluation_runs.csv by jump, loss, point_id, and seeds 100–129. '
         'point_id encodes P/A/eta. T=60 s, dt=.01 s, epsilon=.5 m, C=3200 bit/s, data/ACK=32/16 B, '
         'forward/ACK extra delay=.05/.02 s, reliable ACK and stop-and-wait. Fees include failed data attempts and generated ACKs. '
         'The CSV retains all 144 selections, including 5 infeasible records with blank estimates (not zeros).']
    (ROOT/'report_results_table.md').write_text('\n'.join(md)+'\n',encoding='utf-8')

    ablation=[]
    # Fixed eta and paired seeds: 12 conditions x 5 eta x 5 A = 300 contrasts.
    for j in (0,.5,1,2):
        for loss in (0,.1,.3):
            for eta in (.05,.1,.2,.5,1):
                e=next(rr for key,rr in bypoint.items() if key[:2]==(j,loss) and rr[0]['policy']=='error' and rr[0]['error_threshold']==eta)
                for age in (.25,.5,1,2,4):
                    ea=next(rr for key,rr in bypoint.items() if key[:2]==(j,loss) and rr[0]['policy']=='error_age' and rr[0]['error_threshold']==eta and rr[0]['max_age']==age)
                    r=dict(jump=j,loss=loss,eta=eta,max_age=age,n=30,E_point=e[0]['point_id'],EA_point=ea[0]['point_id'])
                    for m in FIELDS:
                        r['E_'+m]=float(np.mean([v[m] for v in e]));r['EA_'+m]=float(np.mean([v[m] for v in ea]))
                        mean,lo,hi=bootstrap([a[m]-b[m] for a,b in zip(ea,e)],indices)
                        r.update({'delta_'+m:mean,'delta_'+m+'_lo':lo,'delta_'+m+'_hi':hi})
                    r['same_rmse_seeds_tol1e12']=sum(abs(a['rmse_m']-b['rmse_m'])<=1e-12 for a,b in zip(ea,e))
                    r['same_bytes_seeds_exact']=sum(a['total_bytes']==b['total_bytes'] for a,b in zip(ea,e))
                    er='same' if abs(r['delta_rmse_m'])<=1e-12 else 'lower' if r['delta_rmse_m']<0 else 'higher'
                    cr='same' if abs(r['delta_bytes_per_s'])<=1e-12 else 'lower' if r['delta_bytes_per_s']<0 else 'higher'
                    r['mean_relation']='RMSE_'+er+'__cost_'+cr
                    ablation.append(r)
    assert len(ablation)==300
    write_csv(OUT/'fixed_eta_ablation.csv',ablation)
    relations=sorted({r['mean_relation'] for r in ablation})
    text=['# E / EA 固定阈值消融（既有v0.2数据）', '',
          '2026-11-03。没有新增仿真。固定相同η和相同seed，只改变EA的年龄上限A；与按预算分别调优的E/EA候选比较严格区分。'
          '12条件×5个η×5个A=300个配对比较，每比较30seed。这是第三阶段描述性分析，不是预注册的300项确认性检验。', '',
          '差值定义EA−E。RMSE/字节率均值关系的“相同”以绝对1e−12判定（只为浮点容差）；原始字节计数按整数精确比较。'
          '均值关系不是显著性判断；另附逐seed差值的95%bootstrap区间，未做多重比较校正。', '',
          '## 12条件概览（每行25个固定η/A比较）', '',
          '|Jump m/s|Loss|'+'|'.join(relations)+'|', '|---|---|'+'|'.join(['---']*len(relations))+'|']
    for j in (0,.5,1,2):
        for loss in (0,.1,.3):
            counts=Counter(r['mean_relation'] for r in ablation if r['jump']==j and r['loss']==loss)
            text.append('|%g|%g|'%(j,loss)+'|'.join(str(counts[k]) for k in relations)+'|')
    text+=['','## 固定η=.2 m：A=1与4 s的完整切片', '',
           '|Jump|Loss|A/s|E RMSE/m|EA RMSE/m|E B/s|EA B/s|EA−E RMSE [95%CI]/m|', '|---|---|---|---|---|---|---|---|']
    for r in ablation:
        if r['eta']==.2 and r['max_age'] in (1,4):
            text.append('|%g|%g|%g|%.5f|%.5f|%.3f|%.3f|%.5f [%.5f,%.5f]|'%(r['jump'],r['loss'],r['max_age'],r['E_rmse_m'],r['EA_rmse_m'],r['E_bytes_per_s'],r['EA_bytes_per_s'],r['delta_rmse_m'],r['delta_rmse_m_lo'],r['delta_rmse_m_hi']))
    text+=['','完整300行（四指标E/EA均值、配对差和区间、逐seed相同数）见 `results/report_v03/fixed_eta_ablation.csv`。'
           '均值相同不保证每seed相同，请同时检查same_rmse_seeds_tol1e12和same_bytes_seeds_exact。', '',
           '解释限于携带准确瞬时速度的分段恒速模型：没有机动时E无需发送；EA可以保持同样准确而增加费用。'
           '存在机动/丢包时，额外年龄更新改变后续采样时刻和所经历的按时间信道，可能同时改变精度与费用；'
           '不要用一个重合工作点推断全部年龄保护无效，也不要把低误差的均值关系直接称为普遍优势或显著结论。']
    (ROOT/'ablation_E_EA_v03.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    assert all(sha(ROOT/p)==h for p,h in frozen.items())
    manifest=dict(version='report-evidence-v0.3',model_version='0.2',new_simulations=0,python=sys.version,numpy=np.__version__,
        bootstrap_replicates=10000,bootstrap_seed=20261103,frozen_artifacts_verified=len(frozen),
        ablation_comparisons=300,selection_records=144,source_csv_sha256=sha(SRC/'evaluation_runs.csv'),
        generator_sha256=sha(Path(__file__)),outputs={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'report_selected_results.csv',OUT/'fixed_eta_ablation.csv',ROOT/'report_results_table.md',ROOT/'ablation_E_EA_v03.md']})
    (OUT/'evidence_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Frozen hashes verified:',len(frozen));print(Counter(r['mean_relation'] for r in ablation))

if __name__=='__main__':main()
