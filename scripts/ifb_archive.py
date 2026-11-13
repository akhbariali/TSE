"""Separate IFB daily-report archive. Run to download/index all exposed daily pages.
Use --limit 20 for a recent sample, or --import-files PATH ... for local Excel files.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import fcntl
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
import time
from urllib.parse import urlencode, urljoin, urlsplit, parse_qs
from urllib.request import Request, build_opener, HTTPCookieProcessor
from http.cookiejar import CookieJar
from analyze_reports import workbook, normalized, checked_values
from download_reports import ROOT, atomic_json, read_json, workbook_bytes
from index_reports import init_db as base_init, connect, normalize

FOLDER = ROOT/'data/ifb'
DB = FOLDER/'archive.sqlite3'
PAGE = 'https://www.ifb.ir/datareporter/periodicalreport.aspx'
PARSER_VERSION = 1
FLOW_KEYS = ['turnover_rial','volume','retail_buy_rial','institutional_buy_rial','retail_sell_rial',
             'institutional_sell_rial','retail_net_rial','retail_net_volume','retail_buy_value_share',
             'retail_sell_value_share','retail_flow_turnover_ratio','retail_buy_vwap_rial',
             'retail_sell_vwap_rial','institutional_buy_vwap_rial','institutional_sell_vwap_rial']


def init_db():
    base_init(DB)
    with connect(DB) as db:
        db.executescript('''CREATE TABLE IF NOT EXISTS ifb_prices (
          workbook_sha TEXT REFERENCES workbooks(sha) ON DELETE CASCADE,
          date TEXT, symbol TEXT, payload TEXT, PRIMARY KEY(workbook_sha,symbol));
          CREATE TABLE IF NOT EXISTS ifb_metadata (
          workbook_sha TEXT REFERENCES workbooks(sha) ON DELETE CASCADE,
          symbol TEXT, payload TEXT, PRIMARY KEY(workbook_sha,symbol));''')


def date(value):
    value = str(value).translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789'))
    match = re.search(r'((?:13|14)\d{2})[./-]?(\d{2})[./-]?(\d{2})',value)
    if not match:
        raise ValueError('No IFB report date')
    return '/'.join(match.groups())


def col_number(col):
    result=0
    for char in col: result=result*26+ord(char)-64
    return result


def parse(path):
    sheets=workbook(path, all_sheets=True)
    sheet_name,rows=next(iter(sheets.items()))
    kind='flows' if 'حقوق' in normalized(sheet_name) else 'prices' if 'قیمت' in normalized(sheet_name) else None
    if kind is None: raise ValueError('Unsupported IFB worksheet')
    header_index,header=next((i,r) for i,r in rows.items() if any('کد فارسی نماد' in normalized(v) for v in r.values()))
    symbol_col=next(c for c,v in header.items() if 'کد فارسی نماد' in normalized(v))
    def header_col(label):
        return next(c for c,v in header.items() if label in normalized(v))
    company_col=header_col('نام شرکت');market_col=header_col('نام بازار');sub_col=header_col('نام زیرگروه')
    # B11/D11 identify the report date; B7 in the price file is the comparison start.
    title=rows.get(11,{})
    report_date=date(title.get('D') or title.get('B') or path.name)
    if kind=='flows':
        start=date(rows.get(7,{}).get('B',report_date));end=date(rows.get(8,{}).get('B',report_date))
        if start!=end: raise ValueError('Multi-day ownership report excluded from daily history')
        report_date=end
        groups=rows.get(header_index-2,{});investors=rows.get(header_index-1,{})
        def previous(mapping,col):
            options=[(col_number(c),normalized(v)) for c,v in mapping.items() if col_number(c)<=col_number(col)]
            return max(options)[1] if options else ''
        fields={};totals={}
        for c,v in header.items():
            group=previous(groups,c);investor=previous(investors,c);label=normalized(v)
            if group=='کل' and label in ('حجم','ارزش'):
                totals[investor,label]=c
            if group not in ('خرید','فروش') or investor not in ('حقیقی','حقوقی'): continue
            field={'حجم':'volume','ارزش':'value','تعداد نفرات':'count'}.get(label)
            if field: fields[group,investor,field]=c
        def amount(row,side,investor,field):
            value=Decimal(row.get(fields[side,investor,field], '0'))
            if not value.is_finite() or value<0: raise ValueError('Invalid negative/non-finite amount')
            return value
    else:
        fields={name:header_col(label) for name,label in {
            'turnover_rial':'ارزش معاملات','volume':'حجم معاملات','closing_price_rial':'قیمت پایانی انتهای',
            'last_price_rial':'قیمت آخرین معامله','source_average_price_rial':'قیمت میانگین'}.items()}
    records=[];issues=[];market=submarket='';seen=set();duplicates=set()
    for index,row in sorted(rows.items()):
        if index<=header_index:continue
        if row.get(market_col):
            market=row[market_col];submarket=''
        submarket=row.get(sub_col) or submarket
        symbol=row.get(symbol_col)
        if not symbol or not row.get(company_col) or not re.search(r'[\u0621-\u06ff]',symbol) or not re.search(r'\d$',symbol):continue
        if symbol in seen: duplicates.add(symbol)
        seen.add(symbol)
        record={'date':report_date,'symbol':symbol,'company':row[company_col],'market':market,'submarket':submarket}
        try:
            if kind=='flows':
                rb,ib,rs,ins=[amount(row,side,investor,'value') for side,investor in [('خرید','حقیقی'),('خرید','حقوقی'),('فروش','حقیقی'),('فروش','حقوقی')]]
                checked_values(dict(zip(['D','E','H','I'],[rb,ib,rs,ins])))
                for investor in ('خریداران','فروشندگان'):
                    c=totals.get((investor,'ارزش'))
                    if c and c in row and abs(Decimal(row[c])-rb-ib)>max(Decimal(1),(rb+ib)*Decimal('1e-14')):
                        raise ValueError('Investor value columns disagree with row total')
                try:
                    rbv,ibv,rsv,isv=[amount(row,side,investor,'volume') for side,investor in [('خرید','حقیقی'),('خرید','حقوقی'),('فروش','حقیقی'),('فروش','حقوقی')]]
                    checked_values(dict(zip(['D','E','H','I'],[rbv,ibv,rsv,isv])),volume=True)
                    for investor in ('خریداران','فروشندگان'):
                        c=totals.get((investor,'حجم'))
                        if c and c in row and Decimal(row[c])!=rbv+ibv:raise ValueError('Volume differs from source row total')
                except Exception:
                    rbv=ibv=rsv=isv=None;issues.append(f'{symbol}: volume unavailable; value retained')
                total=rb+ib;quantity=rbv+ibv if rbv is not None else None
                record.update(turnover_rial=total,volume=quantity,retail_buy_rial=rb,institutional_buy_rial=ib,
                    retail_sell_rial=rs,institutional_sell_rial=ins,retail_net_rial=rb-rs,
                    retail_net_volume=rbv-rsv if rbv is not None else None,
                    retail_buy_value_share=rb/total if total else None,retail_sell_value_share=rs/total if total else None,
                    retail_flow_turnover_ratio=(rb-rs)/total if total else None,
                    retail_buy_vwap_rial=rb/rbv if rbv else None,retail_sell_vwap_rial=rs/rsv if rsv else None,
                    institutional_buy_vwap_rial=ib/ibv if ibv else None,institutional_sell_vwap_rial=ins/isv if isv else None)
                for side,label in [('خرید','buy'),('فروش','sell')]:
                    for investor,category in [('حقیقی','retail'),('حقوقی','institutional')]:
                        try:record[f'{category}_{label}_count']=amount(row,side,investor,'count')
                        except Exception:record[f'{category}_{label}_count']=None
            else:
                for field,c in fields.items():
                    try:
                        value=Decimal(row[c])
                        if not value.is_finite() or value<0:raise ValueError('Invalid price')
                        record[field]=value
                    except Exception:
                        record[field]=None;issues.append(f'{symbol}: {field} unavailable')
                if record['volume'] and record['turnover_rial'] is not None:
                    record['average_price_rial']=record['turnover_rial']/record['volume']
                else:record['average_price_rial']=None
            records.append(record)
        except Exception as exc:issues.append(f'Excluded {symbol}: {exc}')
    if duplicates:
        records=[r for r in records if r['symbol'] not in duplicates]
        issues.extend(f'Excluded ambiguous duplicate symbol {symbol}' for symbol in sorted(duplicates))
    if not records:raise ValueError('No usable IFB symbol rows')
    # Last summary row has the exchange-wide total as its final numeric cell.
    summary=next((r for _,r in reversed(sorted(rows.items())) if normalized(r.get('A','')) in ('فرابورس ایران','جمع کل')),None)
    if summary:
        try:
            source_total=Decimal(summary[max(summary,key=col_number)])
            retained_total=sum(r['turnover_rial'] or 0 for r in records)
            if abs(source_total-retained_total)>max(Decimal(1),abs(source_total)*Decimal('1e-14')):
                issues.append(f'Retained turnover differs from published total: {retained_total} vs {source_total}; incomplete coverage')
        except Exception:issues.append('Published summary total unavailable')
    return kind,report_date,records,issues


def ingest(path, report_id=None, source_url=None, report_date_hint=None, retry=False):
    init_db();digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with connect(DB) as db:
        prior=db.execute('SELECT parser_version,source_name,report_id FROM workbooks WHERE sha=?',(digest,)).fetchone()
        if prior and prior['parser_version']==PARSER_VERSION and not retry:
            if report_id and report_id>(prior['report_id'] or 0):db.execute('UPDATE workbooks SET report_id=?,detail_url=? WHERE sha=?',(report_id,source_url or PAGE,digest))
            return
    error=None
    try:kind,day,records,issues=parse(path)
    except Exception as exc:
        kind,day,records,issues='unsupported',date(report_date_hint) if report_date_hint else None,[],[]
        error=f'{type(exc).__name__}: {exc}'
    retained=FOLDER/'raw'/f'{digest}.xlsx';retained.parent.mkdir(parents=True,exist_ok=True)
    if not retained.exists():retained.write_bytes(path.read_bytes())
    total=sum(r['turnover_rial'] or 0 for r in records);net=sum(r.get('retail_net_rial',0) for r in records)
    positive=sum(r.get('retail_net_rial',0)>0 for r in records);negative=sum(r.get('retail_net_rial',0)<0 for r in records)
    daily={'date':day,'file':path.name,'symbols':len(records),'turnover_rial':total,'volume':sum(r['volume'] or 0 for r in records),
        'retail_net_rial':net,'retail_net_positive_symbols':positive,'retail_net_negative_symbols':negative,
        'retail_net_zero_symbols':len(records)-positive-negative,'top10_turnover_share':sum(sorted((r['turnover_rial'] or 0 for r in records),reverse=True)[:10])/total if total else None,
        'partial':bool(issues),'validation_issues':len(issues)}
    source_name=prior['source_name'] if prior else f'IFB {day} {kind}.xlsx' if path.name.startswith('download-') else path.name
    now=datetime.now(timezone.utc).isoformat();state=('partial' if issues else 'ready') if kind=='flows' else 'reference' if kind=='prices' else 'unsupported'
    with connect(DB) as db:
        db.execute('DELETE FROM workbooks WHERE sha=?',(digest,))
        db.execute('''INSERT INTO workbooks (sha,file,source_name,report_id,title,effective_date,published_at,detail_url,bytes,date,state,error,issues,daily,parser_version,indexed_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(digest,str(retained.relative_to(ROOT)),source_name,report_id,
          f'IFB {kind} · {day}',day,None,source_url or PAGE,retained.stat().st_size,day,state,error,json.dumps(issues,ensure_ascii=False),json.dumps(daily,default=str),PARSER_VERSION,now))
        if kind=='flows':
            keys=['workbook_sha','symbol','company','search_text',*FLOW_KEYS]
            db.executemany(f'INSERT INTO flows ({",".join(keys)}) VALUES ({",".join("?" for _ in keys)})',
                [(digest,r['symbol'],r['company'],normalize(r['symbol']+' '+r['company']),*[float(r[k]) if r[k] is not None else None for k in FLOW_KEYS]) for r in records])
            db.executemany('INSERT INTO ifb_metadata VALUES (?,?,?)',[(digest,r['symbol'],json.dumps({k:v for k,v in r.items() if k not in FLOW_KEYS},default=str,ensure_ascii=False)) for r in records])
        elif kind=='prices':db.executemany('INSERT INTO ifb_prices VALUES (?,?,?,?)',[(digest,day,r['symbol'],json.dumps(r,default=str,ensure_ascii=False)) for r in records])
    manifest=read_json(FOLDER/'download-manifest.json',[])
    manifest=[e for e in manifest if e.get('sha256')!=digest]
    manifest.append({'sha256':digest,'file':str(retained.relative_to(ROOT)),'report_id':report_id,'kind':kind,'date':day,'source_name':source_name,'url':source_url or PAGE})
    atomic_json(FOLDER/'download-manifest.json',manifest)
    print(f'{state}: IFB {kind} {day}: {len(records)} rows, {len(issues)} issues',flush=True)


class Listing(HTMLParser):
    def __init__(self):
        super().__init__();self.hidden={};self.reports=[];self.pages=set();self.in_grid=False;self.row=None;self.cells=[];self.cell=None;self.links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='input' and attrs.get('type')=='hidden' and attrs.get('name'):self.hidden[attrs['name']]=attrs.get('value','')
        if tag=='table' and attrs.get('id')=='ContentPlaceHolder1_grdPRs':self.in_grid=True
        if not self.in_grid:return
        if tag=='tr':self.cells=[];self.links=[]
        if tag=='td':self.cell=[]
        if tag=='a':
            href=attrs.get('href','');match=re.search(r'Page\$(\d+)',href)
            if match:self.pages.add(int(match[1]))
            if 'GetPeriodicalFile.aspx' in href and 'type=Excel' in href and 'none' not in attrs.get('style',''):self.links.append(urljoin(PAGE,href))
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag=='td' and self.cell is not None:self.cells.append(' '.join(''.join(self.cell).split()));self.cell=None
        if tag=='tr' and self.links and len(self.cells)>=7:
            if 'روزانه' in self.cells[2]:
                for link in self.links:self.reports.append({'url':link,'date':self.cells[3],'title':self.cells[6],'id':int(parse_qs(urlsplit(link).query)['id'][0])})
        # The grid contains a nested pager table. Its closing tag must not end parsing.


def sync(limit=0,retry=False):
    init_db()
    with (FOLDER/'download.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Another IFB update is running')
        for entry in read_json(FOLDER/'download-manifest.json',[]):
            local=ROOT/entry['file']
            if local.exists():ingest(local,entry.get('report_id'),entry.get('url'),entry.get('date'),retry)
        opener=build_opener(HTTPCookieProcessor(CookieJar()))
        def request(url,data=None):
            for attempt in range(3):
                try:
                    with opener.open(Request(url,data=data,headers={'User-Agent':'Market archive research/1.0','Referer':PAGE}),timeout=40) as response:return response.read()
                except Exception:
                    if attempt==2:raise
                    time.sleep(2**attempt)
        status={'phase':'catalog','processed':0,'attachments_total':0,'pages_scanned':0,'pages_total':0};errors=[];catalog={};seen=set()
        atomic_json(FOLDER/'download-status.json',status)
        try:
            page=Listing();page.feed(request(PAGE).decode('utf-8-sig'))
            fields={**page.hidden,'ctl00$ContentPlaceHolder1$comboReportType':'1','ctl00$ContentPlaceHolder1$comboReportPeriod':'10','ctl00$ContentPlaceHolder1$BtnSearch':'جستجو'}
            page=Listing();page.feed(request(PAGE,urlencode(fields).encode()).decode('utf-8-sig'))
            number=1
            while True:
                status.update(phase='downloading',pages_scanned=number,pages_total=max(page.pages or {number}))
                for report in page.reports:
                    if report['id'] in seen:continue
                    seen.add(report['id']);catalog[str(report['id'])]=report
                    if not ('حقیقی' in report['title'] or 'حقيقي' in report['title'] or 'قیمت' in report['title'] or 'قيمت' in report['title']):continue
                    existing=next((e for e in read_json(FOLDER/'download-manifest.json',[]) if e.get('report_id')==report['id']),None)
                    if existing and (ROOT/existing['file']).exists():
                        ingest(ROOT/existing['file'],report['id'],report['url'],report['date'])
                    else:
                        try:
                            body=request(report['url']);workbook_bytes(body,'.xlsx')
                            path=FOLDER/f"download-{report['id']}.xlsx";path.write_bytes(body)
                            try:ingest(path,report['id'],report['url'],report['date'])
                            finally:path.unlink(missing_ok=True)
                        except Exception as exc:errors.append({**report,'error':str(exc)})
                    status['processed']+=1;status['attachments_total']=status['processed']
                    atomic_json(FOLDER/'download-status.json',status);atomic_json(FOLDER/'download-errors.json',errors)
                    if limit and status['processed']>=limit:break
                previous=read_json(FOLDER/'report-catalog.json',{}).get('reports',{})
                atomic_json(FOLDER/'report-catalog.json',{'total_count':len(previous.keys()|catalog.keys()),'reports':{**previous,**catalog}})
                if (limit and status['processed']>=limit) or number+1 not in page.pages:break
                number+=1
                fields={**page.hidden,'ctl00$ContentPlaceHolder1$comboReportType':'1','ctl00$ContentPlaceHolder1$comboReportPeriod':'10',
                        '__EVENTTARGET':'ctl00$ContentPlaceHolder1$grdPRs','__EVENTARGUMENT':f'Page${number}'}
                following=Listing();following.feed(request(PAGE,urlencode(fields).encode()).decode('utf-8-sig'))
                if {r['id'] for r in following.reports} and {r['id'] for r in following.reports}.issubset(seen):raise ValueError('IFB pagination repeated a page; archive remains incomplete')
                page=following
            status.update(phase='complete',updated_at=datetime.now(timezone.utc).isoformat())
        except Exception as exc:
            status.update(phase='failed',error=str(exc));errors.append({'error':str(exc)})
        atomic_json(FOLDER/'download-status.json',status);atomic_json(FOLDER/'download-errors.json',errors)
        if status['phase']=='failed':raise RuntimeError(status['error'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--limit',type=int,default=0);parser.add_argument('--import-files',nargs='+',type=Path);parser.add_argument('--retry-errors',action='store_true')
    args=parser.parse_args()
    if args.import_files:
        for path in args.import_files:ingest(path)
    else:sync(args.limit,args.retry_errors)
