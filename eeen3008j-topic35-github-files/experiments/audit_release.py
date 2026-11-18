"""Audit the actual saved release; write a traceable output/source inventory."""
import csv,json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/v0.2'
def read(name):return list(csv.DictReader((OUT/name).open(encoding='utf-8-sig')))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=json.loads((ROOT/'results/v0.1_smoke/manifest.json').read_text())
    assert all(digest(ROOT/n)==h for n,h in old['source_sha256'].items())
    release=json.loads((OUT/'manifest.json').read_text())
    assert all(digest(ROOT/n)==h for n,h in release['source_sha256'].items())
    from scan_v02 import points,point_id,hashes
    assert hashes()==release['source_sha256']
    groups={}
    for split,count,seeds in [('tuning',4800,set(range(10))),('evaluation',14400,set(range(100,130)))]:
        rows=read(split+'_runs.csv');assert len(rows)==count
        seen=set()
        for r in rows:
            key=(float(r['jump']),float(r['loss']),int(r['seed']),r['point_id'])
            assert key not in seen;seen.add(key)
            assert int(r['decision_mismatches'])==0
            assert int(r['attempts'])==int(r['lost'])+int(r['delivered'])+int(r['data_inflight'])
            assert int(r['ack_generated'])==int(r['ack_delivered'])+int(r['ack_inflight'])
            assert int(r['total_bytes'])==32*int(r['attempts'])+16*int(r['ack_generated'])
            for name in ['rmse_m','bytes_per_s','mean_aoi_s','over_tolerance_s']:
                assert math.isfinite(float(r[name])) and float(r[name])>=0
            if float(r['jump'])==0 and r['policy']=='error':assert float(r['rmse_m'])==0 and int(r['total_bytes'])==0
            groups.setdefault((split,r['jump'],r['loss'],r['point_id']),set()).add(int(r['seed']))
        assert all(g==seeds for k,g in groups.items() if k[0]==split)
    for name,n in [('slice_runs.csv',720),('deterministic_runs.csv',16),('dt_sensitivity.csv',36),('workpoint_summary.csv',480)]:
        assert len(read(name))==n
    for r in read('workpoint_summary.csv'):
        for m in ('rmse_m','bytes_per_s','over_tolerance_s','mean_aoi_s'):
            assert float(r[m+'_lo'])<=float(r[m+'_hi'])
    selections=json.loads((OUT/'selected_configs.json').read_text())
    assert len(selections)==144 and sum(s['point_id'] is None for s in selections)==5
    for name in ('01_tradeoff','02_maneuver','03_delay_slices'):
        for ext in ('png','pdf','svg'):assert (ROOT/'figures/v0.2'/(name+'.'+ext)).stat().st_size>1000
    files=list(ROOT.glob('*.py'))+list(ROOT.glob('*v02*.md'))+list((ROOT/'configs').glob('*v02*'))
    files+=list((ROOT/'figures/v0.2').glob('*'))+list((ROOT/'tables/v0.2').glob('*'))
    files+=list(OUT.glob('*.csv'))+list(OUT.glob('*.json'))
    files=[p for p in files if p.name!='release_audit.json']
    result=dict(status='passed',v01_preserved=True,tuning_runs=4800,evaluation_runs=14400,
                supplementary_runs=772,decision_mismatches=0,infeasible_selections=5,
                source_and_output_sha256={str(p.relative_to(ROOT)):digest(p) for p in files})
    (OUT/'release_audit.json').write_text(json.dumps(result,indent=2))
    for stage in ('scan','statistics','supplement','plot','audit'):
        p=OUT/(stage+'_failures.log')
        if not p.exists():p.write_text('')
    print('RELEASE AUDIT PASSED')
if __name__=='__main__':main()
