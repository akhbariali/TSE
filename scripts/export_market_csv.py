"""Stream the complete active market archive to one atomically replaced CSV.

No recommendation logic, period selection, or fund exclusion is applied.
"""
import argparse
import csv
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from download_reports import ROOT

FLOW_FIELDS=['turnover_rial','volume','retail_buy_rial','institutional_buy_rial','retail_sell_rial',
 'institutional_sell_rial','retail_net_rial','retail_net_volume','retail_buy_value_share',
 'retail_sell_value_share','retail_flow_turnover_ratio','retail_buy_vwap_rial','retail_sell_vwap_rial',
 'institutional_buy_vwap_rial','institutional_sell_vwap_rial']
FIELDS=['market','date','gregorian_date','symbol','company','instrument_code','isin','security_type','is_fund',
 'source',*FLOW_FIELDS,'average_price_rial','closing_price_rial','last_price_rial','source_average_price_rial',
 'retail_buy_count','retail_sell_count','institutional_buy_count','institutional_sell_count',
 'source_market','submarket','report_state','report_id','source_name','source_sha','source_url','published_at',
 'price_source_sha','extra_source_fields_json']
COUNT_ALIASES={'buy_I_Count':'retail_buy_count','sell_I_Count':'retail_sell_count',
 'buy_N_Count':'institutional_buy_count','sell_N_Count':'institutional_sell_count'}


def market_rows(root,market,path):
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=30)
    db.row_factory=sqlite3.Row
    try:
        db.execute('BEGIN')
        reports=db.execute('SELECT * FROM active_reports ORDER BY date,sha').fetchall()
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for report in reports:
            api={};metadata={};prices={}
            if report['source']=='tsetmc':
                snapshot=json.loads((root/report['file']).read_text())
                if snapshot['date']!=report['date'] or snapshot['market']!=market:raise ValueError('Source snapshot identity mismatch')
                api={r['symbol']:r for r in snapshot['records']}
            elif market=='ifb':
                if 'ifb_metadata' in tables:
                    metadata={r['symbol']:json.loads(r['payload']) for r in db.execute('SELECT symbol,payload FROM ifb_metadata WHERE workbook_sha=?',(report['sha'],))}
                if 'ifb_prices' in tables:
                    for price in db.execute('''SELECT p.symbol,p.payload,p.workbook_sha FROM ifb_prices p JOIN workbooks w ON w.sha=p.workbook_sha
                      WHERE p.date=? ORDER BY COALESCE(w.report_id,0) DESC,w.indexed_at DESC''',(report['date'],)):
                        prices.setdefault(price['symbol'],price)
            for flow in db.execute('SELECT * FROM flows WHERE workbook_sha=? ORDER BY symbol',(report['sha'],)):
                source=api.get(flow['symbol']) if api else metadata.get(flow['symbol'],{})
                if report['source']=='tsetmc' and source is None:raise ValueError('Flow absent from original API snapshot')
                source=source or {};row={key:flow[key] for key in flow.keys() if key in FIELDS}
                extra={}
                for key,value in source.items():
                    target=COUNT_ALIASES.get(key,key)
                    if key=='market':row['source_market']=value
                    elif target in FIELDS:row[target]=value
                    elif key not in ('display_symbol','date','symbol','company'):extra[key]=value
                quote=prices.get(flow['symbol'])
                if quote:
                    values=json.loads(quote['payload'])
                    for key in ('closing_price_rial','last_price_rial','source_average_price_rial'):row[key]=values.get(key)
                    row['price_source_sha']=quote['workbook_sha']
                row['market']=market
                row.update(date=report['date'],source=report['source'],report_state=report['state'],report_id=report['report_id'],
                    source_name=report['source_name'],source_sha=report['sha'],source_url=report['detail_url'],published_at=report['published_at'])
                if row.get('volume') is not None and float(row['volume'])>0:row['average_price_rial']=float(row['turnover_rial'])/float(row['volume'])
                row['extra_source_fields_json']=json.dumps(extra,ensure_ascii=False,sort_keys=True) if extra else ''
                yield row
    finally:db.close()


def export_all(root=ROOT,output=None):
    root=Path(root);output=Path(output) if output else root/'data/exports/TSE-IFB-market-data.csv'
    databases=[('tse',root/'data/archive.sqlite3'),('ifb',root/'data/ifb/archive.sqlite3')]
    if any(not path.is_file() for _,path in databases):raise FileNotFoundError('Both market databases are required; previous CSV retained')
    # Serialize exporters only. Each database is read in a transaction, so an
    # ongoing collector can publish a later revision without exposing half-written rows.
    output.parent.mkdir(parents=True,exist_ok=True)
    lock=(output.parent/'.market-csv.lock').open('a')
    try:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Another market CSV export is running')
        count={};latest={};old=output.stat().st_size if output.exists() else 0
        descriptor,name=tempfile.mkstemp(prefix=output.name+'.',suffix='.tmp',dir=output.parent)
        try:
            with os.fdopen(descriptor,'w',encoding='utf-8-sig',newline='') as handle:
                writer=csv.DictWriter(handle,fieldnames=FIELDS,extrasaction='raise');writer.writeheader()
                for market,path in databases:
                    count[market]=0
                    for row in market_rows(root,market,path):
                        writer.writerow(row);count[market]+=1;latest[market]=row['date']
                    if not count[market]:raise ValueError(f'{market} has no usable rows; previous CSV retained')
                handle.flush();os.fsync(handle.fileno())
            os.replace(name,output)
        finally:
            if os.path.exists(name):os.unlink(name)
        return {'file':str(output),'rows':count,'latest_date':latest,'bytes':output.stat().st_size,'replaced_previous_bytes':old}
    finally:
        if lock:lock.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();print(json.dumps(export_all(output=args.output),ensure_ascii=False))
