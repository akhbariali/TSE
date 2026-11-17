"""Explainable retail-buying research candidates; no price/return prediction."""
from statistics import mean, median

BASELINE=20
RECENT=5
SCALE_FLOOR=.05


def assess(history, as_of):
    """Compare five observed sessions with the preceding twenty, never future rows.

    Input rows must be chronological, finite, and have positive turnover. Missing
    sessions are not zero-filled. Use a five percentage-point dispersion floor
    so a near-flat history cannot produce an arbitrarily large score.
    """
    if len(history)<BASELINE+RECENT:return {'eligible':False,'reason':'Needs 25 valid observations'}
    baseline=history[-(BASELINE+RECENT):-RECENT];recent=history[-RECENT:]
    if recent[-1]['date']!=as_of:return {'eligible':False,'reason':'No observation on the selected latest report date'}
    def ratio(row):return row['retail_net_rial']/row['turnover_rial']
    ratios=[ratio(r) for r in baseline];center=median(ratios)
    scale=max(SCALE_FLOOR,1.4826*median(abs(r-center) for r in ratios))
    recent_ratios=[ratio(r) for r in recent];average=mean(recent_ratios)
    shift=average-center;trend_z=shift/scale;latest=recent_ratios[-1];spike_z=(latest-center)/scale
    buying_days=sum(r['retail_net_rial']>0 for r in recent)
    net=sum(r['retail_net_rial'] for r in recent)
    sustained=buying_days>=4 and net>0 and average>=.05 and shift>=.10 and trend_z>=2
    spike=net>0 and recent[-1]['retail_net_rial']>0 and latest>=.10 and latest-center>=.15 and spike_z>=3
    reasons=[]
    if sustained:reasons.append('Sustained buying: at least 4 of 5 positive sessions and a stronger net/value ratio than its baseline')
    if spike:reasons.append('Unusual latest buying: net/value ratio at least 15 percentage points above its baseline')
    sources={r.get('source','excel') for r in baseline+recent}
    partial=sum(r.get('report_state')=='partial' for r in baseline+recent)
    return {'eligible':True,'recommended':bool(reasons),'reasons':reasons,
        'score':round(max(trend_z,spike_z),3),'trend_score':round(trend_z,3),
        'latest_ratio':latest,'recent_ratio':average,'baseline_ratio':center,
        'shift_percentage_points':shift*100,'buying_days':buying_days,'recent_net_rial':net,
        'baseline_start':baseline[0]['date'],'baseline_end':baseline[-1]['date'],
        'recent_start':recent[0]['date'],'as_of':as_of,'baseline_observations':BASELINE,'recent_observations':RECENT,
        'mixed_sources':len(sources)>1,'partial_reports':partial}
