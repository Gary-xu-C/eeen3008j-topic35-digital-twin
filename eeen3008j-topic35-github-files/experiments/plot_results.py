"""Report figures from persisted, reviewed v0.2 rows; no simulation in plotting."""
import sys,json,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.deps'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze_results import read,group,bootstrap,METRICS
from scan_v02 import OUT,write_csv

FIG=ROOT/'figures/v0.2';TABLE=ROOT/'tables/v0.2'
COLORS={'periodic':'#2471A3','age':'#B8860B','error':'#677832','error_age':'#B34D83'}
MARKERS={'periodic':'o','age':'s','error':'^','error_age':'D'}
LABELS={'periodic':'P','age':'A','error':'E','error_age':'EA'}
POLICIES=list(COLORS)
def save(fig,name):
    for ext in ('png','pdf','svg'):fig.savefig(FIG/(name+'.'+ext),dpi=220,bbox_inches='tight')
    plt.close(fig)

def main():
    FIG.mkdir(parents=True,exist_ok=True);TABLE.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.grid':True,'grid.alpha':.2,'svg.fonttype':'none'})
    summary=read(OUT/'workpoint_summary.csv')
    fig,axes=plt.subplots(2,3,figsize=(12,6),constrained_layout=True,sharex=True,sharey='row')
    chartrows=[]
    for i,jump in enumerate((0,2)):
        for col,loss in enumerate((0,.1,.3)):
            ax=axes[i,col]
            for policy in POLICIES:
                rr=[r for r in summary if r['jump']==jump and r['loss']==loss and r['policy']==policy]
                chartrows+=rr
                for k,r in enumerate(rr):
                    ax.errorbar(r['bytes_per_s_mean'],r['rmse_m_mean'],
                        xerr=[[max(0,r['bytes_per_s_mean']-r['bytes_per_s_lo'])],[max(0,r['bytes_per_s_hi']-r['bytes_per_s_mean'])]],
                        yerr=[[max(0,r['rmse_m_mean']-r['rmse_m_lo'])],[max(0,r['rmse_m_hi']-r['rmse_m_mean'])]],
                        fmt=MARKERS[policy],color=COLORS[policy],mfc='none',markersize=5,alpha=.8,
                        linewidth=.7,label=LABELS[policy] if k==0 else None)
            ax.set_title(f'|delta v|={jump} m/s; loss={loss:g}')
            ax.set_xlim(left=-3)
            if i==0:ax.set_ylim(-.02,.12)
            else:
                ax.set_yscale('symlog',linthresh=.1)
                ax.set_ylim(0,17)
                ax.set_yticks([0,.1,.5,1,5,15],['0','0.1','0.5','1','5','15'])
            if col==0:ax.set_ylabel('Position RMSE (m)')
            if i==1:ax.set_xlabel('Total logical byte rate (B/s)')
    axes[0,0].legend(ncol=4,loc='upper left',fontsize=9)
    axes[1,0].set_ylabel('RMSE (m; symlog, linear below 0.1)')
    fig.suptitle('All workpoints in shown conditions: mean and pointwise 95% seed-bootstrap CI\n30 paired seeds; descriptive trade-off; lower row uses symlog; no simultaneous band',fontsize=11)
    save(fig,'01_tradeoff');write_csv(TABLE/'figure01_data.csv',chartrows)

    fig,axes=plt.subplots(4,1,figsize=(9,8),sharex=True,constrained_layout=True)
    styles={'periodic':'-','age':'--','error':':','error_age':'-.'}
    for policy in POLICIES:
        rr=read(OUT/('maneuver_'+policy+'_trace.csv'))
        x=[r['time_s'] for r in rr]; kwargs=dict(color=COLORS[policy],ls=styles[policy],label=LABELS[policy])
        axes[0].plot(x,[r['estimate_m'] for r in rr],**kwargs)
        axes[1].plot(x,[r['error_m'] for r in rr],**kwargs)
        axes[2].plot(x,[r['aoi_s'] for r in rr],**kwargs)
        events=json.loads((OUT/('maneuver_'+policy+'_events.json')).read_text())
        at=[0.];total=[0]
        for event in events:
            if event['event'] in ('send','ack_generated'):
                at.append(event['time_s']);total.append(total[-1]+event['bytes'])
        at.append(60.0);total.append(total[-1])
        axes[3].step(at,total,where='post',**kwargs)
    axes[0].plot(x,[r['position_m'] for r in rr],color='#333333',ls=(0,(5,4)),label='True')
    axes[0].legend(ncol=5,loc='upper left')
    for ax,label in zip(axes,['Position (m)','Absolute error (m)','Receiver AoI (s)','Cumulative bytes (B)']):
        ax.set_ylabel(label);ax.set_xlim(3.8,6.5);ax.axvline(4.3,color='#555555',lw=.7)
    axes[0].set_ylim(3,12)
    axes[2].set_ylim(0,5)
    axes[3].set_ylim(0,400)
    axes[1].axhline(.5,color='#333333',ls='--',lw=.8,label='Tolerance 0.5 m')
    axes[1].legend(loc='upper right');axes[3].set_xlabel('Time (s)')
    fig.suptitle('Prespecified single manoeuvre, seed 100: P=A=1 s, eta=0.2 m\nVelocity 1 to 3 m/s at 4.3 s; E/EA position errors and P/A traces overlap',fontsize=11)
    save(fig,'02_maneuver')

    slices=read(OUT/'slice_runs.csv');rng=np.random.default_rng(20261103);indices=rng.integers(0,30,(10000,30))
    stats=[]
    for (kind,value,policy),rr in group(slices,['slice','value','policy']).items():
        row=dict(slice=kind,value=value,policy=policy,n=30,point_id=rr[0]['point_id'])
        rr=sorted(rr,key=lambda r:r['seed'])
        for metric in METRICS:
            mean,lo,hi=bootstrap([r[metric] for r in rr],indices)
            row.update({metric+'_mean':mean,metric+'_lo':lo,metric+'_hi':hi})
        stats.append(row)
    write_csv(OUT/'slice_summary.csv',stats)
    fig,axes=plt.subplots(2,4,figsize=(13,6),constrained_layout=True)
    fields=[('rmse_m','RMSE (m)'),('bytes_per_s','Total byte rate (B/s)'),('over_tolerance_s','Time above 0.5 m (s)'),('mean_aoi_s','Mean AoI (s)')]
    for row,kind in enumerate(('delay','ack_delay')):
        for col,(metric,label) in enumerate(fields):
            ax=axes[row,col]
            for policy in POLICIES:
                rr=sorted([r for r in stats if r['slice']==kind and r['policy']==policy],key=lambda r:r['value'])
                y=np.array([r[metric+'_mean'] for r in rr]);lo=np.array([r[metric+'_lo'] for r in rr]);hi=np.array([r[metric+'_hi'] for r in rr])
                ax.errorbar([r['value'] for r in rr],y,yerr=[np.maximum(0,y-lo),np.maximum(0,hi-y)],
                    color=COLORS[policy],marker=MARKERS[policy],ls=styles[policy],label=LABELS[policy],capsize=2)
            ax.set_title(label);ax.set_xlabel(('Forward extra delay' if kind=='delay' else 'ACK extra delay')+' (s)')
            ax.set_ylim(bottom=0)
    axes[0,0].legend(ncol=4,fontsize=8)
    fig.suptitle('Delay slices: |delta v|=2 m/s, loss=0.1, n=30; pointwise 95% CI\nConfigurations frozen on tuning seeds under 48 B/s; actual evaluation rates vary',fontsize=11)
    save(fig,'03_delay_slices')
    (FIG/'provenance.json').write_text(json.dumps({
        '01_tradeoff':'results/v0.2/workpoint_summary.csv -> tables/v0.2/figure01_data.csv; all points for jump 0 and 2',
        '02_maneuver':'results/v0.2/maneuver_*_trace.csv and *_events.json; prespecified seed100, deterministic single jump',
        '03_delay_slices':'results/v0.2/slice_runs.csv -> slice_summary.csv; tuning-selected configs fixed',
        'exports':['PDF','SVG','PNG'],'matplotlib':matplotlib.__version__,'numpy':np.__version__},indent=2))
    print('9 figure exports complete')

if __name__=='__main__': main()
