"""Frozen v0.2 tuning/evaluation scan, streamed metrics, resumable per batch."""
import csv, hashlib, json, platform, time, traceback
from pathlib import Path
from dataclasses import asdict
from concurrent.futures import ProcessPoolExecutor
from simulator_v02 import Config, simulate, make_trajectory, make_channel

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/v0.2'

def points():
    values=(.25,.5,1,2,4)
    errors=(.05,.1,.2,.5,1)
    return ([('periodic',p,1,.2) for p in values] + [('age',1,a,.2) for a in values]
            + [('error',1,1,e) for e in errors]
            + [('error_age',1,a,e) for a in values for e in errors])

def point_id(p):
    return '%s_P%g_A%g_E%g'%p

def batch(task):
    split,jump,loss,seed=task
    c=Config(duration=60,seed=seed,loss=loss)
    tr=make_trajectory(c,'random_maneuver',jump=jump)
    ch=make_channel(c)
    rows=[]
    for point in points():
        policy,period,age,error=point
        cfg=Config(**(asdict(c)|dict(period=period,max_age=age,error_threshold=error)))
        m=simulate(cfg,policy,tr,ch,record=False)['metrics']
        rows.append(dict(split=split,jump=jump,loss=loss,seed=seed,point_id=point_id(point),
                         period=period,max_age=age,error_threshold=error,**m))
    return rows

def write_csv(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def hashes():
    files=list(ROOT.glob('*v02.py'))+[ROOT/'configs/formal_v02.json']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

def main():
    import argparse
    a=argparse.ArgumentParser(); a.add_argument('--benchmark',action='store_true'); a.add_argument('--workers',type=int,default=4)
    args=a.parse_args(); OUT.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'configs/formal_v02.json').read_text())
    if args.benchmark:
        start=time.perf_counter(); rows=batch(('tuning',2,.1,0))
        info=dict(runs=len(rows),elapsed_s=time.perf_counter()-start,config_frozen=config,source_sha256=hashes())
        (OUT/'benchmark.json').write_text(json.dumps(info,indent=2)); print(info['elapsed_s'],flush=True); return
    source=hashes(); lock=OUT/'scan_lock.json'
    if lock.exists() and json.loads(lock.read_text())!=source: raise RuntimeError('Source changed; use a fresh version/output directory')
    lock.write_text(json.dumps(source,indent=2))
    tasks=[(split,j,l,s) for split,seeds in [('tuning',range(10)),('evaluation',range(100,130))]
           for j in config['jumps'] for l in config['losses'] for s in seeds]
    directory=OUT/'batches'; directory.mkdir(exist_ok=True)
    def filename(t): return directory/('%s_j%g_l%g_s%d.json'%t)
    todo=[t for t in tasks if not filename(t).exists()]
    start=time.perf_counter()
    try:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for i,(t,rows) in enumerate(zip(todo,pool.map(batch,todo,chunksize=1))):
                filename(t).write_text(json.dumps(rows))
                if i%12==0: print(f'batches {i+1}/{len(todo)} ({time.perf_counter()-start:.1f}s)',flush=True)
    except Exception:
        with (OUT/'failures.log').open('a') as f: f.write(traceback.format_exc())
        raise
    rows=[r for t in tasks for r in json.loads(filename(t).read_text())]
    for split in ('tuning','evaluation'): write_csv(OUT/(split+'_runs.csv'),[r for r in rows if r['split']==split])
    assert len(rows)==19200 and len({(r['split'],r['jump'],r['loss'],r['seed'],r['point_id']) for r in rows})==19200
    manifest=dict(status='completed',version='0.2',python=platform.python_version(),elapsed_this_invocation_s=time.perf_counter()-start,
                  config=config,source_sha256=source,tuning_runs=4800,evaluation_runs=14400,
                  files_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*_runs.csv')},
                  failure_count=0,decision_mismatches=sum(r['decision_mismatches'] for r in rows))
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)); print('COMPLETED',len(rows),flush=True)

if __name__=='__main__': main()
