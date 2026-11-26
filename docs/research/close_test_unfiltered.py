import pandas as pd,numpy as np,lightgbm as lgb
from sklearn.metrics import roc_auc_score,average_precision_score
p='/mnt/data/TSE-IFB-market-data.csv'; cols=['date','market','symbol','source','volume','turnover_rial','retail_flow_turnover_ratio','retail_buy_value_share','retail_sell_value_share','closing_price_rial','average_price_rial']
d=pd.read_csv(p,usecols=cols,low_memory=False)
d=d[(d.closing_price_rial>0)&(d.average_price_rial>0)&(d.volume>0)&(d.turnover_rial>1e9)].copy();d['key']=d.market+'|'+d.symbol
all_dates=sorted(pd.read_csv(p,usecols=['date']).date.unique());idx={t:i for i,t in enumerate(all_dates)};d['idx']=d.date.map(idx);d=d.sort_values(['key','idx']);g=d.groupby('key',sort=False)
d['next']=g.closing_price_rial.shift(-1)/d.closing_price_rial-1
# global day gap compare
nidx=g.idx.shift(-1);d.loc[nidx-d.idx!=1,'next']=np.nan
for lag in [1,2,5,10]:
 prev=g.closing_price_rial.shift(lag);days=g.idx.shift(lag)
 d[f'r{lag}']=(d.closing_price_rial/prev-1).where(d.idx-days<=lag+2).clip(-.4,.4)
for c in ['retail_flow_turnover_ratio','turnover_rial']:
 if c=='turnover_rial':d['logturn']=np.log1p(d[c]);c='logturn'
 for l in [1,5]:d[c+'lag'+str(l)]=g[c].shift(l)
d['spread']=(d.closing_price_rial/d.average_price_rial-1).clip(-.2,.2)
d=d[d.next.notna()].copy()
d['target']=(d.next>=.02).astype(int)
f=['retail_flow_turnover_ratio','retail_buy_value_share','retail_sell_value_share','logturn','spread','r1','r2','r5','r10','retail_flow_turnover_ratiolag1','retail_flow_turnover_ratiolag5','logturnlag1','logturnlag5']
dates=sorted(d.date.unique());cut1=dates[int(len(dates)*.5)];cut2=dates[int(len(dates)*.7)];tr=d[d.date<cut1];va=d[(d.date>=cut1)&(d.date<cut2)];te=d[d.date>=cut2]
m=lgb.LGBMClassifier(n_estimators=230,num_leaves=12,min_child_samples=130,learning_rate=.035,reg_lambda=10,verbosity=-1,n_jobs=4);m.fit(tr[f],tr.target,eval_set=[(va[f],va.target)],callbacks=[lgb.early_stopping(20,verbose=False)])
pred=m.predict_proba(te[f])[:,1];te=te.copy();te['pred']=pred
print('close-only split',cut1,cut2,'sizes',len(tr),len(va),len(te),'base',te.target.mean(),'auc',roc_auc_score(te.target,pred),'ap',average_precision_score(te.target,pred))
for sc in ['pred','r1','r5','retail_flow_turnover_ratio']:
 s=te.sort_values(['date',sc],ascending=[True,False]).groupby('date').head(10)
 print(sc,len(s),'precision',s.target.mean(),'mean_close_return',s.next.mean(),'mean_market',te.next.mean(),'positive', (s.next>0).mean())
