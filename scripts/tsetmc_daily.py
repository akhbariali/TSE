"""Fetch dated actual retail values from TSETMC; retain Excel history separately.

python3 scripts/tsetmc_daily.py --start 2026-11-14
Daily reruns retry the last seven calendar days and unresolved dates since cutover.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from download_reports import ROOT, atomic_json, read_json
from index_reports import init_db, connect, normalize
import ifb_archive

BASE='https://cdn.tsetmc.com/api/'
FOLDER=ROOT/'data/tsetmc'
CUTOVER=date(2026,11,14)
FLOW_KEYS=['turnover_rial','volume','retail_buy_rial','institutional_buy_rial','retail_sell_rial',
 'institutional_sell_rial','retail_net_rial','retail_net_volume','retail_buy_value_share',
 'retail_sell_value_share','retail_flow_turnover_ratio','retail_buy_vwap_rial','retail_sell_vwap_rial',
 'institutional_buy_vwap_rial','institutional_sell_vwap_rial','instrument_code','is_fund',
 'closing_price_rial','last_price_rial']


def jalali(day):
    gy=day.year-1600;gm=day.month-1;gd=day.day-1
    days=365*gy+(gy+3)//4-(gy+99)//100+(gy+399)//400
    days+=sum([31,28,31,30,31,30,31,31,30,31,30,31][:gm])+gd
    if gm>1 and day.year%4==0 and (day.year%100!=0 or day.year%400==0):days+=1
    days-=79;cycles,days=divmod(days,12053);jy=979+33*cycles
    cycles,days=divmod(days,1461);jy+=4*cycles
    if days>=366:
        cycles,days=divmod(days-1,365);jy+=cycles
    if days<186:jm,jd=divmod(days,31);jm+=1
    else:jm,jd=divmod(days-186,30);jm+=7
    return f'{jy:04}/{jm:02}/{jd+1:02}'


def as_number(value, field):
    if value is None:raise ValueError(f'Missing {field}')
    n=Decimal(str(value))
    if not n.is_finite() or n<0:raise ValueError(f'Invalid {field}')
    return n


def instruments(payload):
    rows=payload.get('marketwatch')
    if not isinstance(rows,list) or not rows:raise ValueError('Market-watch schema changed or empty universe')
    selected={}
    for row in rows:
        # Official flow 1 = TSE; 2 = IFB; 4 = IFB base. Other flows include derivatives/commodity markets.
        flow=int(row.get('flow',0));kind=int(row.get('yVal',0));isin=row.get('insID','')
        if flow not in (1,2,4) or kind not in (300,303,309,313,400,403,404,305) or not isin.endswith('1'):continue
        code=str(row['insCode']);symbol=row.get('lva','').strip();company=row.get('lvc','').strip()
        if not code.isdigit() or not symbol or not company:raise ValueError('Incomplete instrument identity')
        selected[code]={'instrument_code':code,'symbol':symbol+'1','display_symbol':symbol,'company':company,
            'market':'tse' if flow==1 else 'ifb','is_fund':int(kind==305),'security_type':kind,'isin':isin}
    if not selected:raise ValueError('No supported primary instruments found')
    return list(selected.values())


def observation(instrument, client_payload, closing_payload, day):
    closing=closing_payload.get('closingPriceDaily');client=client_payload.get('clientType')
    if not isinstance(closing,dict):raise ValueError('Missing dated closing record')
    stamp=int(day.strftime('%Y%m%d'));code=instrument['instrument_code']
    if int(closing.get('dEven',0))!=stamp or str(closing.get('insCode'))!=code:raise ValueError('Closing date/instrument mismatch')
    turnover=as_number(closing.get('qTotCap'),'qTotCap');quantity=as_number(closing.get('qTotTran5J'),'qTotTran5J')
    if quantity==0 and turnover==0:return None
    if quantity<=0 or turnover<=0:raise ValueError('Trading value and volume must both be positive')
    if not isinstance(client,dict) or int(client.get('recDate',0))!=stamp or str(client.get('insCode'))!=code:raise ValueError('Client date/instrument mismatch')
    rb,ib,rs,ins=[as_number(client.get(k),k) for k in ['buy_I_Value','buy_N_Value','sell_I_Value','sell_N_Value']]
    rbv,ibv,rsv,isv=[as_number(client.get(k),k) for k in ['buy_I_Volume','buy_N_Volume','sell_I_Volume','sell_N_Volume']]
    tolerance=max(Decimal(1),turnover*Decimal('1e-12'))
    if abs(rb+ib-rs-ins)>tolerance or abs(rb+ib-turnover)>tolerance:raise ValueError('Client value/closing totals do not reconcile')
    if rbv+ibv!=rsv+isv or rbv+ibv!=quantity:raise ValueError('Client volume/closing totals do not reconcile')
    if any(v!=v.to_integral_value() for v in [rbv,ibv,rsv,isv]):raise ValueError('Fractional volume')
    record={**instrument,'date':jalali(day),'gregorian_date':day.isoformat(),
        'turnover_rial':rb+ib,'volume':quantity,'retail_buy_rial':rb,'institutional_buy_rial':ib,
        'retail_sell_rial':rs,'institutional_sell_rial':ins,'retail_net_rial':rb-rs,'retail_net_volume':rbv-rsv,
        'retail_buy_value_share':rb/turnover,'retail_sell_value_share':rs/turnover,'retail_flow_turnover_ratio':(rb-rs)/turnover,
        'retail_buy_vwap_rial':rb/rbv if rbv else None,'retail_sell_vwap_rial':rs/rsv if rsv else None,
        'institutional_buy_vwap_rial':ib/ibv if ibv else None,'institutional_sell_vwap_rial':ins/isv if isv else None,
        'closing_price_rial':as_number(closing.get('pClosing'),'pClosing'),'last_price_rial':as_number(closing.get('pDrCotVal'),'pDrCotVal'),
        'net_retail_flow_billion_toman':(rb-rs)/Decimal(10_000_000_000)}
    for field in ['buy_I_Count','buy_N_Count','sell_I_Count','sell_N_Count']:
        record[field]=as_number(client.get(field),field)
    return record


class Client:
    def __init__(self,rate=8,ttl=3600):
        self.rate=rate;self.ttl=ttl;self.lock=threading.Lock();self.next_call=0
        (FOLDER/'cache').mkdir(parents=True,exist_ok=True);(FOLDER/'raw').mkdir(exist_ok=True)
    def get(self,path):
        url=BASE+path;key=hashlib.sha256(url.encode()).hexdigest();cache=FOLDER/'cache'/f'{key}.json'
        stored=read_json(cache,{})
        if stored and time.time()-stored['fetched_at']<self.ttl:return stored['body'],stored['raw_sha']
        for attempt in range(4):
            with self.lock:
                pause=max(0,self.next_call-time.monotonic());self.next_call=max(time.monotonic(),self.next_call)+1/self.rate
            if pause:time.sleep(pause)
            try:
                with urlopen(Request(url,headers={'User-Agent':'TSE-IFB archive research/1.0','Accept':'application/json','Referer':'https://www.tsetmc.com/'}),timeout=25) as response:
                    body=response.read()
                payload=json.loads(body,parse_float=Decimal)
                if not isinstance(payload,dict):raise ValueError('Unexpected JSON shape')
                digest=hashlib.sha256(body).hexdigest();raw=FOLDER/'raw'/f'{digest}.json.gz'
                if not raw.exists():
                    temporary=raw.with_suffix(f'.{threading.get_ident()}.tmp');temporary.write_bytes(gzip.compress(body));temporary.replace(raw)
                # JSON cache uses source decimal strings to avoid losing source precision.
                atomic_json(cache,{'url':url,'fetched_at':time.time(),'body':json.loads(json.dumps(payload,default=str)),'raw_sha':digest})
                return payload,digest
            except Exception:
                if attempt==3:raise
                time.sleep(min(2**attempt,8))


def classify(universe):
    for market,db_path in [('tse',ROOT/'data/archive.sqlite3'),('ifb',ifb_archive.DB)]:
        with connect(db_path) as db:
            if market=='ifb':
                db.execute("UPDATE flows SET is_fund=1 WHERE is_fund IS NULL AND EXISTS(SELECT 1 FROM ifb_metadata m WHERE m.workbook_sha=flows.workbook_sha AND m.symbol=flows.symbol AND instr(m.payload,'صندوق')>0)")
            for item in universe:
                if item['market']!=market:continue
                # Explicit current primary-market aliases; exact historical suffixes stay distinct.
                for alias in (item['symbol'],item['display_symbol']):
                    db.execute('INSERT OR REPLACE INTO instrument_classification VALUES (?,?,?,?,?)',
                        (normalize(alias),item['instrument_code'],item['is_fund'],item['security_type'],datetime.now(timezone.utc).isoformat()))


def publish(market,day,records,issues,expected,skipped,limited=False):
    if not records:return False
    # A failed/limited fetch must not activate a tiny replacement for a whole market day.
    failures=[i for i in issues if not i['reason'].startswith('No dated closing observation')]
    if limited or len(failures)>max(2,expected*.1):return False
    day_text=jalali(day);db_path=ROOT/'data/archive.sqlite3' if market=='tse' else ifb_archive.DB
    records=sorted(records,key=lambda r:r['instrument_code'])
    issues=sorted(issues,key=lambda i:(i['symbol'],i['reason']))
    payload={'source':'tsetmc','date':day_text,'gregorian_date':day.isoformat(),'market':market,
        'universe':'Primary shares, rights and funds; current instrument membership','records':records,
        'expected_instruments':expected,'no_trade_instruments':skipped,'issues':issues}
    serial=json.dumps(payload,ensure_ascii=False,default=str,sort_keys=True);digest=hashlib.sha256(serial.encode()).hexdigest()
    folder=ROOT/'data' if market=='tse' else ifb_archive.FOLDER
    snapshot=folder/'api'/f'{day.isoformat()}-{digest}.json';snapshot.parent.mkdir(parents=True,exist_ok=True)
    snapshot.write_text(serial)
    total=sum(r['turnover_rial'] for r in records);net=sum(r['retail_net_rial'] for r in records)
    positive=sum(r['retail_net_rial']>0 for r in records);negative=sum(r['retail_net_rial']<0 for r in records)
    daily={'date':day_text,'file':snapshot.name,'source':'tsetmc','symbols':len(records),'turnover_rial':total,
        'volume':sum(r['volume'] for r in records),'retail_net_rial':net,'retail_net_positive_symbols':positive,
        'retail_net_negative_symbols':negative,'retail_net_zero_symbols':len(records)-positive-negative,
        'top10_turnover_share':sum(sorted((r['turnover_rial'] for r in records),reverse=True)[:10])/total if total else None,
        'partial':bool(issues),'validation_issues':len(issues),'expected_instruments':expected,'no_trade_instruments':skipped}
    now=datetime.now(timezone.utc).isoformat();columns=['workbook_sha','symbol','company','search_text',*FLOW_KEYS]
    with connect(db_path) as db:
        if db.execute('SELECT 1 FROM workbooks WHERE sha=?',(digest,)).fetchone():return True
        prior=db.execute("SELECT json_extract(daily,'$.symbols') FROM active_reports WHERE date=? AND source='tsetmc'",(day_text,)).fetchone()
        if prior and len(records)<prior[0]*.8:return False
        db.execute('''INSERT INTO workbooks (sha,file,source_name,title,effective_date,published_at,detail_url,bytes,date,state,issues,daily,parser_version,indexed_at,source)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(digest,str(snapshot.relative_to(ROOT)),f'TSETMC {day_text.replace(chr(47),chr(45))}.json',f'TSETMC {market.upper()} daily values',
          day_text,now,'https://www.tsetmc.com/MarketWatchNew',snapshot.stat().st_size,day_text,'partial' if issues else 'ready',
          json.dumps(issues,ensure_ascii=False),json.dumps(daily,default=str),1,now,'tsetmc'))
        db.executemany(f'INSERT INTO flows ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',
            [(digest,r['symbol'],r['company'],normalize(r['symbol']+' '+r['company']),
              *[r[k] if k in ('instrument_code','is_fund') else float(r[k]) if r[k] is not None else None for k in FLOW_KEYS]) for r in records])
    return True


def sync(start=CUTOVER,end=None,limit=0,rate=8,workers=4,ttl=3600):
    init_db();ifb_archive.init_db();FOLDER.mkdir(parents=True,exist_ok=True)
    with (FOLDER/'sync.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Another TSETMC sync is running')
        client=Client(rate,ttl);now=datetime.now(ZoneInfo('Asia/Tehran'));end=end or now.date()
        if end<start:raise ValueError('End precedes start')
        status={'phase':'discovering','started_at':now.isoformat(),'source':'tsetmc','processed':0,'requested_start':start.isoformat(),'requested_end':end.isoformat()}
        atomic_json(FOLDER/'status.json',status)
        try:
            body,_=client.get('ClosingPrice/GetMarketWatch');universe=instruments(body);classify(universe)
            # Recheck recent dates; completed older dates need no repeated requests.
            checkpoint=read_json(FOLDER/'checkpoint.json',{})
            days=[];day=start
            while day<=end:
                if day.weekday() not in (3,4) and (day>=end-timedelta(days=6) or not checkpoint.get(day.isoformat())):days.append(day)
                day+=timedelta(days=1)
            chosen=universe[:limit] if limit else universe
            status.update(phase='fetching',instruments=len(universe),total=len(chosen)*len(days),dates=[jalali(d) for d in days]);atomic_json(FOLDER/'status.json',status)
            for day in days:
                groups={'tse':[],'ifb':[]};issues={'tse':[],'ifb':[]};no_trade={'tse':0,'ifb':0};stamp=day.strftime('%Y%m%d')
                def fetch(item):
                    path=f"ClosingPrice/GetClosingPriceDaily/{item['instrument_code']}/{stamp}"
                    close,cs=client.get(path);closing=close.get('closingPriceDaily')
                    if isinstance(closing,dict) and int(closing.get('dEven',0))==int(stamp) and Decimal(str(closing.get('qTotCap',-1)))==0 and Decimal(str(closing.get('qTotTran5J',-1)))==0:return item,None,None
                    if not closing:return item,None,'No dated closing observation (not assumed zero)'
                    raw,rs=client.get(f"ClientType/GetClientTypeHistory/{item['instrument_code']}/{stamp}")
                    record=observation(item,raw,close,day)
                    if record:record.update(client_raw_sha=rs,closing_raw_sha=cs)
                    return item,record,None
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    futures={pool.submit(fetch,item):item for item in chosen}
                    for future in as_completed(futures):
                        item=futures[future];market=item['market']
                        try:
                            _,record,error=future.result()
                            if error:issues[market].append({'symbol':item['symbol'],'reason':error})
                            elif record:groups[market].append(record)
                            else:no_trade[market]+=1
                        except Exception as exc:issues[market].append({'symbol':item['symbol'],'reason':str(exc)})
                        status['processed']+=1
                        if status['processed']%10==0:atomic_json(FOLDER/'status.json',status)
                published={}
                for market in groups:
                    expected=sum(i['market']==market for i in universe)
                    published[market]=publish(market,day,groups[market],issues[market],expected,no_trade[market],bool(limit))
                checkpoint[day.isoformat()]=all(published.values()) and not any(i for group in issues.values() for i in group if not i['reason'].startswith('No dated closing observation'))
                atomic_json(FOLDER/'checkpoint.json',checkpoint)
                status.setdefault('results',[]).append({'date':jalali(day),'published':published,'rows':{k:len(v) for k,v in groups.items()},'no_trade':no_trade,'issues':issues})
                atomic_json(FOLDER/'status.json',status)
            status.update(phase='complete',finished_at=datetime.now(timezone.utc).isoformat());atomic_json(FOLDER/'status.json',status)
        except Exception as exc:
            status.update(phase='failed',error=str(exc));atomic_json(FOLDER/'status.json',status);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',type=date.fromisoformat,default=CUTOVER);parser.add_argument('--end',type=date.fromisoformat)
    parser.add_argument('--limit',type=int,default=0);parser.add_argument('--rate',type=float,default=8);parser.add_argument('--workers',type=int,default=4);parser.add_argument('--cache-seconds',type=int,default=3600)
    args=parser.parse_args()
    if not 0<args.rate<=10 or not 1<=args.workers<=8 or args.limit<0:parser.error('Rate must be 0–10/sec, workers 1–8, limit nonnegative')
    sync(args.start,args.end,args.limit,args.rate,args.workers,args.cache_seconds)
