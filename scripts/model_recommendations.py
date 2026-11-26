"""Use the supplied closing-price features with a fee-aware stock target.

Run with .venv/bin/python scripts/model_recommendations.py after the market CSV export.
The web server does not import the optional machine-learning dependencies.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from trading_fees import BUY, SELL, STOCK_TYPES, TARGET_KIND, SOURCE, break_even

ROOT=Path(__file__).resolve().parents[1]
FEATURES=['retail_flow_turnover_ratio','retail_buy_value_share','retail_sell_value_share',
 'logturn','spread','r1','r2','r5','r10','retail_flow_turnover_ratiolag1',
 'retail_flow_turnover_ratiolag5','logturnlag1','logturnlag5']


def features(data, all_dates):
    import numpy as np
    d=data[(data.closing_price_rial>0)&(data.average_price_rial>0)&(data.volume>0)&(data.turnover_rial>1e9)].copy()
    d['key']=d.market+'|'+d.symbol
    d['idx']=d.date.map({date:i for i,date in enumerate(all_dates)})
    d=d.sort_values(['key','idx']);g=d.groupby('key',sort=False)
    d['next_return']=(g.closing_price_rial.shift(-1)/d.closing_price_rial-1).where(g.idx.shift(-1)-d.idx==1)
    d['next_date']=d.idx.map({i:all_dates[i+1] for i in range(len(all_dates)-1)})
    for lag in [1,2,5,10]:
        d[f'r{lag}']=(d.closing_price_rial/g.closing_price_rial.shift(lag)-1).where(d.idx-g.idx.shift(lag)<=lag+2).clip(-.4,.4)
    d['logturn']=np.log1p(d.turnover_rial)
    for column in ['retail_flow_turnover_ratio','logturn']:
        for lag in [1,5]:d[column+'lag'+str(lag)]=g[column].shift(lag)
    d['spread']=(d.closing_price_rial/d.average_price_rial-1).clip(-.2,.2)
    return d


def build(source, output):
    import lightgbm as lgb
    import pandas as pd
    from sklearn.metrics import roc_auc_score, average_precision_score
    columns=['date','market','symbol','volume','turnover_rial','retail_flow_turnover_ratio',
             'retail_buy_value_share','retail_sell_value_share','closing_price_rial','average_price_rial','is_fund','company','security_type']
    # Keep every market date for gap checks, but retain only eligible rows in
    # memory. The full CSV is larger than the production server's spare RAM.
    parts=[];market_dates=set();security_types={}
    for chunk in pd.read_csv(source,usecols=columns,chunksize=20000):
        market_dates.update(chunk.date.unique())
        for market,symbol,kind in chunk[['market','symbol','security_type']].dropna().itertuples(index=False,name=None):
            security_types[market+'|'+symbol]=int(kind)
        eligible=(chunk.closing_price_rial>0)&(chunk.average_price_rial>0)&(chunk.volume>0)&(chunk.turnover_rial>1e9)
        parts.append(chunk.loc[eligible].copy())
    raw=pd.concat(parts,ignore_index=True);del parts,chunk
    raw['security_type']=(raw.market+'|'+raw.symbol).map(security_types)
    # Stock fees are only valid for confirmed shares/rights. Historical labels
    # without a known classification must not inherit a guessed fee schedule.
    raw=raw[raw.security_type.isin(STOCK_TYPES)&~raw.is_fund.fillna(0).astype(bool)].copy()
    all_dates=sorted(market_dates);d=features(raw,all_dates);del raw
    labeled=d[d.next_return.notna()].copy();dates=sorted(labeled.date.unique())
    if len(dates)<10:raise ValueError('At least ten labeled sessions are needed')
    cut1,cut2=dates[int(len(dates)*.5)],dates[int(len(dates)*.7)]
    # Preserve the initial split across daily refreshes so historical results do not
    # silently become in-sample when the archive grows.
    if output.exists():
        with sqlite3.connect(output) as db:
            previous=json.loads(db.execute('SELECT payload FROM metadata').fetchone()[0])
            cut1,cut2=previous['validation_start'],previous['test_start']
    labeled['target']=(labeled.next_return>labeled.market.map({m:break_even(m) for m in BUY})).astype(int)
    # Purge labels crossing either boundary: even a next-session label must have
    # been observable before validation/test starts.
    train=labeled[(labeled.date<cut1)&(labeled.next_date<cut1)]
    validation=labeled[(labeled.date>=cut1)&(labeled.date<cut2)&(labeled.next_date<cut2)]
    test=labeled[labeled.date>=cut2]
    model=lgb.LGBMClassifier(n_estimators=230,num_leaves=12,min_child_samples=130,
        learning_rate=.035,reg_lambda=10,verbosity=-1,n_jobs=4)
    model.fit(train[FEATURES],train.target,eval_set=[(validation[FEATURES],validation.target)],
        callbacks=[lgb.early_stopping(20,verbose=False)])
    scored=d[d.date>=cut2].copy();scored['probability']=model.predict_proba(scored[FEATURES])[:,1]
    pred=model.predict_proba(test[FEATURES])[:,1]
    metadata={'method':'Closing-price LightGBM · positive after stock fees','target_kind':TARGET_KIND,
        'fee_buy':BUY,'fee_sell':SELL,'fee_source':SOURCE,'fee_checked':'2026-11-25',
        'break_even':{m:break_even(m) for m in BUY},'recommendation_limit':50,'validation_start':cut1,
        'test_start':cut2,'trained_through':str(train.date.max()),'validated_through':str(validation.date.max()),
        'data_through':all_dates[-1],'generated_at':datetime.now(timezone.utc).isoformat(),
        'train_rows':len(train),'validation_rows':len(validation),'test_rows':len(test),
        'roc_auc':float(roc_auc_score(test.target,pred)),'average_precision':float(average_precision_score(test.target,pred)),
        'history_kind':'Retrospective held-out reconstruction; publication-time availability has not been audited.'}
    output.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=output.parent,suffix='.sqlite3');os.close(fd)
    try:
        with sqlite3.connect(name) as db:
            db.execute('CREATE TABLE metadata(payload TEXT NOT NULL)')
            db.execute('INSERT INTO metadata VALUES (?)',(json.dumps(metadata),))
            db.execute('CREATE TABLE scores(market TEXT,date TEXT,symbol TEXT,company TEXT,is_fund INTEGER,probability REAL,closing_price_rial REAL,next_return REAL,next_date TEXT,PRIMARY KEY(market,date,symbol))')
            def clean(v):
                if pd.isna(v):return None
                return v.item() if hasattr(v,'item') else v
            db.executemany('INSERT INTO scores VALUES (?,?,?,?,?,?,?,?,?)',
                ([clean(v) for v in row] for row in scored[['market','date','symbol','company','is_fund','probability','closing_price_rial','next_return','next_date']].itertuples(index=False,name=None)))
            db.execute('CREATE INDEX score_dates ON scores(market,date,probability DESC,symbol)')
        os.replace(name,output)
    finally:
        if os.path.exists(name):os.unlink(name)
    return metadata


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'data/exports/TSE-IFB-market-data.csv')
    parser.add_argument('--output',type=Path,default=ROOT/'data/recommendations/closing-model.sqlite3')
    args=parser.parse_args();print(json.dumps(build(args.source,args.output),ensure_ascii=False,indent=2))
