"""Frozen representative slices; no Cartesian expansion beyond coordination scope."""
import json
from dataclasses import asdict
from scan_v02 import OUT, write_csv
from simulator_v02 import Config, POLICIES, simulate, make_trajectory, make_channel

def main():
    selected=json.loads((OUT/'selected_configs.json').read_text())
    selected={s['policy']:s['point_id'] for s in selected if s['jump']==2 and s['loss']==.1 and s['budget']==48}
    from scan_v02 import points,point_id
    lookup={point_id(p):p for p in points()}
    rows=[]
    for kind,values in [('delay',(0,.05,.2)),('ack_delay',(.02,.2,.8))]:
        for value in values:
            for seed in range(100,130):
                base=Config(duration=60,seed=seed,loss=.1,**{kind:value})
                tr=make_trajectory(base,'random_maneuver',jump=2); ch=make_channel(base)
                for policy in POLICIES:
                    _,p,a,e=lookup[selected[policy]]
                    c=Config(**(asdict(base)|dict(period=p,max_age=a,error_threshold=e)))
                    m=simulate(c,policy,tr,ch,False)['metrics']
                    rows.append(dict(slice=kind,value=value,seed=seed,point_id=selected[policy],**m))
    write_csv(OUT/'slice_runs.csv',rows)
    deterministic=[]
    for scenario in ('constant','maneuver','acceleration','total_loss'):
        for policy in POLICIES:
            c=Config(duration=60,seed=100,loss=1 if scenario=='total_loss' else 0)
            tr=make_trajectory(c,'maneuver' if scenario=='total_loss' else scenario,jump=.5 if scenario=='acceleration' else 2)
            result=simulate(c,policy,tr,make_channel(c))
            deterministic.append(dict(case=scenario,seed=100,**result['metrics']))
            if scenario=='maneuver':
                write_csv(OUT/(scenario+'_'+policy+'_trace.csv'),result['trace'])
                (OUT/(scenario+'_'+policy+'_events.json')).write_text(json.dumps(result['events']))
    write_csv(OUT/'deterministic_runs.csv',deterministic)
    sensitivity=[]
    for dt in (.005,.01,.02):
        for scenario in ('constant','maneuver','acceleration'):
            for policy in POLICIES:
                c=Config(duration=60,dt=dt,seed=100)
                m=simulate(c,policy,make_trajectory(c,scenario,jump=.5 if scenario=='acceleration' else 2),make_channel(c),False)['metrics']
                sensitivity.append(dict(dt=dt,case=scenario,**m))
    write_csv(OUT/'dt_sensitivity.csv',sensitivity)
    print('supplement',len(rows),len(deterministic),len(sensitivity))

if __name__=='__main__': main()
