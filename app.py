"""Password-protected TSE/IFB report browser. Run: python3 app.py --port 8000"""
import argparse
import csv
import fcntl
from datetime import datetime, timezone
import io
import json
import math
import os
from http.cookies import SimpleCookie
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlsplit

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
from download_reports import read_json
from index_reports import connect, init_db, normalize
import ifb_archive
from app_auth import SingleUserAuth, COOKIE, SESSION_SECONDS

STATIC = ROOT / 'web/static'
SYNC_LOCK = threading.Lock()
SYNC_PROCESS = None
IFB_SYNC_PROCESS = None
AUTH = None


def rows(db, sql, params=()):
    return [dict(row) for row in db.execute(sql, params)]


def validate_date(value):
    if value and not re.fullmatch(r'\d{4}/\d{2}/\d{2}', value):
        raise ValueError('Use a Solar Hijri date in YYYY/MM/DD format.')
    return value


def selection(db, query):
    available = rows(db, 'SELECT sha,date,daily,published_at,report_id FROM active_reports ORDER BY date')
    start = validate_date(query.get('start', ''))
    end = validate_date(query.get('end', ''))
    if start and end and start > end:
        raise ValueError('The start date must be before the end date.')
    selected = [r for r in available if (not start or r['date'] >= start) and (not end or r['date'] <= end)]
    window = query.get('window', '20')
    if window != 'all' and not (start or end):
        count = int(window)
        if count < 1 or count > 10000:
            raise ValueError('Invalid report window.')
        selected = selected[-count:]
    return available, selected


def scope_clause(db, query):
    available, selected = selection(db, query)
    if not selected:
        return '0', [], selected
    return 'a.date BETWEEN ? AND ?', [selected[0]['date'], selected[-1]['date']], selected


def scope_info(selected):
    return {'start': selected[0]['date'] if selected else None,
            'end': selected[-1]['date'] if selected else None, 'reports': len(selected)}


def numeric_day(row):
    data = json.loads(row['daily'])
    for key, value in list(data.items()):
        if key not in ('date', 'file') and isinstance(value, str):
            data[key] = float(value)
    data.update(sha=row['sha'], published_at=row['published_at'], report_id=row['report_id'])
    return data


def status(db, market='tse'):
    folder = ifb_archive.FOLDER if market=='ifb' else ROOT/'data'
    download = read_json(folder / 'download-status.json', {})
    if download.get('phase') in ('catalog', 'downloading'):
        # A terminated process can leave an in-progress checkpoint behind.
        # Inspect the OS lock so that the UI can offer resume after a restart.
        try:
            with (folder / 'download.lock').open('r') as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    download = {**download, 'phase': 'interrupted'}
                except BlockingIOError:
                    pass
        except FileNotFoundError:
            download = {**download, 'phase': 'interrupted'}
    indexing = read_json(folder / 'index-status.json', {})
    catalog = read_json(folder / 'report-catalog.json', {})
    manifest = read_json(folder / 'download-manifest.json', [])
    count = dict(db.execute('''SELECT COUNT(*) AS indexed,
              SUM(state='ready') AS ready, SUM(state IN ('warning','partial')) AS warning, SUM(state='partial') AS partial,
              SUM(state='unsupported') AS unsupported FROM workbooks''').fetchone())
    active = dict(db.execute('SELECT COUNT(*) AS reports, MIN(date) AS first_date, MAX(date) AS last_date FROM active_reports').fetchone())
    with SYNC_LOCK:
        process = IFB_SYNC_PROCESS if market=='ifb' else SYNC_PROCESS
        syncing = process is not None and process.poll() is None
    return {'download': download, 'indexing': indexing, 'counts': {**count, **active},
            'downloaded_files': len({e['file'] for e in manifest}), 'attachments': len(manifest),
            'catalog_reports': catalog.get('total_count', 0), 'sync_running': syncing,
            'errors': read_json(folder / 'download-errors.json', []),
            'issues': rows(db, "SELECT sha,source_name,state,error,issues FROM workbooks WHERE state IN ('warning','partial','unsupported') OR (state='reference' AND issues!='[]') ORDER BY effective_date DESC LIMIT 100"),
            'updated_at': datetime.now(timezone.utc).isoformat()}


def overview(db, query):
    available, selected = selection(db, query)
    days = [numeric_day(r) for r in selected]
    aggregate = {'net_rial': sum(d['retail_net_rial'] for d in days),
                 'turnover_rial': sum(d['turnover_rial'] for d in days),
                 'positive_days': sum(d['retail_net_rial'] > 0 for d in days),
                 'negative_days': sum(d['retail_net_rial'] < 0 for d in days),
                 'observations': sum(d['symbols'] for d in days)}
    aggregate['average_turnover_rial'] = aggregate['turnover_rial']/len(days) if days else 0
    return {'scope': scope_info(selected), 'days': days, 'aggregate': aggregate,
            'latest': days[-1] if days else None, 'dates': [r['date'] for r in available],
            'status': status(db, query.get('_market','tse'))}


def flow_query(db, query, export=False):
    clause, params, selected = scope_clause(db, query)
    search = normalize(query.get('q', '').strip())
    if search:
        clause += ' AND instr(f.search_text,?)>0'
        params.append(search)
    direction = query.get('direction', 'all')
    minimum = float(query.get('minimum', '0') or 0)
    if not math.isfinite(minimum) or minimum < 0:
        raise ValueError('Minimum trading value cannot be negative.')
    having = 'SUM(f.turnover_rial)>=?'
    params.append(minimum * 1e13)
    if direction in ('buy', 'sell'):
        having += ' AND SUM(f.retail_net_rial)' + ('>0' if direction == 'buy' else '<0')
    sorting = {'net_desc': 'net_rial DESC', 'net_asc': 'net_rial ASC',
               'turnover': 'turnover_rial DESC', 'ratio': 'flow_ratio DESC',
               'persistence': 'positive_days*1.0/observed_days DESC,net_rial DESC'}
    order = sorting.get(query.get('sort', 'net_desc'), 'net_rial DESC')
    sql = f'''SELECT f.symbol, MAX(f.company) AS company, COUNT(*) AS observed_days, SUM(a.state='partial') AS partial_days,
                SUM(f.turnover_rial) AS turnover_rial, SUM(f.retail_net_rial) AS net_rial,
                SUM(CASE WHEN f.volume>0 THEN f.turnover_rial END)/NULLIF(SUM(CASE WHEN f.volume>0 THEN f.volume END),0) AS average_price_rial,
                SUM(f.retail_buy_rial) AS buy_rial, SUM(f.retail_sell_rial) AS sell_rial,
                SUM(f.retail_net_rial>0) AS positive_days, SUM(f.retail_net_rial<0) AS negative_days,
                SUM(f.retail_net_rial)/NULLIF(SUM(f.turnover_rial),0) AS flow_ratio
              FROM flows f JOIN active_reports a ON f.workbook_sha=a.sha
              WHERE {clause} GROUP BY f.symbol HAVING {having}'''
    total = db.execute('SELECT COUNT(*) FROM ('+sql+')', params).fetchone()[0]
    if export:
        data = rows(db, sql+f' ORDER BY {order},f.symbol', params)
    else:
        page = max(1, int(query.get('page', '1')))
        size = min(100, max(1, int(query.get('size', '25'))))
        data = rows(db, sql+f' ORDER BY {order},f.symbol LIMIT ? OFFSET ?', [*params, size, (page-1)*size])
    return {'items': data, 'total': total, 'scope': scope_info(selected)}


def reports(db, query):
    page = max(1, int(query.get('page', '1')))
    size = min(100, max(1, int(query.get('size', '20'))))
    clause, params = '1', []
    if query.get('q'):
        clause += ' AND (instr(source_name,?)>0 OR instr(title,?)>0 OR instr(COALESCE(date,effective_date),?)>0)'
        params.extend([query['q']]*3)
    for key, operator in [('start', '>='), ('end', '<=')]:
        value = validate_date(query.get(key, ''))
        if value:
            clause += f' AND date{operator}?'
            params.append(value)
    if query.get('state') in ('ready', 'partial', 'warning', 'unsupported', 'reference'):
        clause += ' AND state=?'
        params.append(query['state'])
    total = db.execute('SELECT COUNT(*) FROM workbooks WHERE '+clause, params).fetchone()[0]
    items = rows(db, '''SELECT sha,source_name,title,date,effective_date,published_at,state,error,issues,bytes,
                 detail_url,report_id,EXISTS(SELECT 1 FROM active_reports a WHERE a.sha=workbooks.sha) AS active
                 FROM workbooks WHERE '''+clause+' ORDER BY effective_date DESC,published_at DESC LIMIT ? OFFSET ?',
                 [*params, size, (page-1)*size])
    return {'items': items, 'total': total, 'page': page, 'size': size}


def symbol_detail(db, query):
    symbol = query.get('symbol', '')
    if not symbol:
        raise ValueError('Choose a symbol.')
    clause, params, selected = scope_clause(db, query)
    data = rows(db, f'''SELECT a.date,a.sha,a.published_at,a.state AS report_state,f.*,
                        f.turnover_rial/NULLIF(f.volume,0) AS average_price_rial FROM flows f
                        JOIN active_reports a ON a.sha=f.workbook_sha
                        WHERE {clause} AND f.symbol=? ORDER BY a.date''', [*params, symbol])
    if query.get('_market')=='ifb':
        for day in data:
            metadata=db.execute('SELECT payload FROM ifb_metadata WHERE workbook_sha=? AND symbol=?',(day['sha'],symbol)).fetchone()
            if metadata:
                details=json.loads(metadata['payload'])
                day.update({k:float(v) if k.endswith('_count') and v is not None else v for k,v in details.items() if k not in ('date','symbol','company')})
            quote_row=db.execute('''SELECT p.payload,p.workbook_sha FROM ifb_prices p JOIN workbooks w ON w.sha=p.workbook_sha
                WHERE p.date=? AND p.symbol=? ORDER BY COALESCE(w.report_id,0) DESC,w.indexed_at DESC LIMIT 1''',(day['date'],symbol)).fetchone()
            if quote_row:
                quotes=json.loads(quote_row['payload'])
                for key in ('closing_price_rial','last_price_rial','source_average_price_rial'):
                    value=quotes.get(key);day[key]=float(value) if value is not None else None
                day['price_sha']=quote_row['workbook_sha']
    return {'symbol': symbol, 'company': data[-1]['company'] if data else '',
            'scope': scope_info(selected), 'days': data,
            'net_rial': sum(r['retail_net_rial'] for r in data),
            'turnover_rial': sum(r['turnover_rial'] for r in data),
            'positive_days': sum(r['retail_net_rial'] > 0 for r in data),
            'negative_days': sum(r['retail_net_rial'] < 0 for r in data)}


class Handler(BaseHTTPRequestHandler):
    timeout = 15
    def send(self, data, code=200, content_type='application/json; charset=utf-8', headers=None):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
        elif isinstance(data, str):
            data = data.encode()
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def session_token(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            return cookie[COOKIE].value if COOKIE in cookie else ''
        except Exception:
            return ''

    def require_login(self):
        if AUTH is None:
            self.send({'error': 'Login is not configured.'}, 503)
            return False
        if AUTH.authenticated(self.session_token()):
            return True
        if urlsplit(self.path).path.startswith('/api/'):
            self.send({'error': 'Please sign in.'}, 401)
        else:
            self.send('', 303, headers={'Location': '/login'})
        return False

    def secure_request(self):
        return self.client_address[0] in ('127.0.0.1', '::1') and self.headers.get('X-Forwarded-Proto') == 'https'

    def session_cookie(self, token, logout=False):
        return f'{COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={0 if logout else SESSION_SECONDS}' + ('; Secure' if self.secure_request() else '')

    def same_origin(self):
        origin = self.headers.get('Origin')
        return self.headers.get('Sec-Fetch-Site') != 'cross-site' and (not origin or (urlsplit(origin).scheme in ('http','https') and urlsplit(origin).netloc == self.headers.get('Host')))

    def login_page(self, code=200, limited=False):
        page = (STATIC/'login.html').read_text()
        if code != 200:
            marker = 'class="login-limit"' if limited else 'class="login-error"'
            page = page.replace(marker + ' role="alert" hidden', marker + ' role="alert"')
        return self.send(page, code, 'text/html; charset=utf-8')

    def do_GET(self):
        try:
            parsed = urlsplit(self.path)
            query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
            route = parsed.path
            if route == '/healthz':
                return self.send({'ok': AUTH is not None}, 200 if AUTH is not None else 503)
            if route == '/login':
                if AUTH is not None and AUTH.authenticated(self.session_token()):
                    return self.send('',303,headers={'Location':'/'})
                return self.login_page()
            if route != '/static/style.css' and not self.require_login():
                return
            if route in ('/', '/index.html'):
                return self.send((STATIC/'index.html').read_bytes(), content_type='text/html; charset=utf-8')
            if route.startswith('/static/'):
                name = route.removeprefix('/static/')
                allowed = {'app.js': 'text/javascript', 'style.css': 'text/css'}
                if name not in allowed:
                    return self.send({'error': 'File not found.'}, 404)
                return self.send((STATIC/name).read_bytes(), content_type=allowed[name]+'; charset=utf-8')
            market='ifb' if route.startswith('/api/ifb/') else 'tse'
            if market=='ifb':
                route=route.replace('/api/ifb/','/api/',1)
            query['_market']=market
            with connect(ifb_archive.DB) if market=='ifb' else connect() as db:
                if route == '/api/overview':
                    result = overview(db, query)
                elif route == '/api/status':
                    result = status(db, market)
                elif route == '/api/flows':
                    result = flow_query(db, query)
                elif route == '/api/reports':
                    result = reports(db, query)
                elif route == '/api/symbol':
                    result = symbol_detail(db, query)
                elif route in ('/api/export/flows', '/api/export/daily'):
                    result = flow_query(db, query, export=True)['items'] if route.endswith('flows') else overview(db, query)['days']
                    output = io.StringIO()
                    output.write('\ufeff')
                    if result:
                        writer = csv.DictWriter(output, fieldnames=list(result[0]))
                        writer.writeheader()
                        writer.writerows(result)
                    return self.send(output.getvalue(), content_type='text/csv; charset=utf-8',
                                     headers={'Content-Disposition': f'attachment; filename="{market}-{route.rsplit("/",1)[-1]}.csv"'})
                elif route.startswith('/api/files/'):
                    digest = route.removeprefix('/api/files/')
                    record = db.execute('SELECT file,source_name FROM workbooks WHERE sha=?', (digest,)).fetchone()
                    if not record:
                        return self.send({'error': 'Workbook not found.'}, 404)
                    path = (ROOT/record['file']).resolve()
                    if not path.is_relative_to(((ifb_archive.FOLDER/'raw') if market=='ifb' else (ROOT/'data/raw')).resolve()) or not path.is_file():
                        return self.send({'error': 'Workbook is unavailable on disk. Refresh the archive to retry.'}, 404)
                    content_type = 'application/vnd.ms-excel' if path.suffix=='.xls' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    return self.send(path.read_bytes(), content_type=content_type,
                                     headers={'Content-Disposition': "attachment; filename*=UTF-8''"+quote(record['source_name'])})
                else:
                    return self.send({'error': 'Page not found.'}, 404)
            return self.send(result)
        except (ValueError, OverflowError) as error:
            self.send({'error': str(error)}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as error:
            print(f'Request error: {error}', file=sys.stderr, flush=True)
            self.send({'error': 'The report could not be loaded. Please try again.'}, 500)

    def do_POST(self):
        global SYNC_PROCESS, IFB_SYNC_PROCESS
        endpoint=urlsplit(self.path).path
        if not self.same_origin():
            return self.send({'error':'Cross-origin request rejected.'},403)
        if endpoint=='/login':
            if AUTH is None:
                return self.send({'error':'Login is not configured.'},503)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if size<=0 or size>8192 or self.headers.get('Content-Type','').split(';')[0]!='application/x-www-form-urlencoded':
                    return self.send({'error':'Invalid login request.'},400)
                form=parse_qs(self.rfile.read(size).decode('utf-8'),max_num_fields=5)
                username=form.get('username',[''])[0];password=form.get('password',[''])[0]
                if len(username)>200 or len(password)>1024:return self.login_page(401)
            except (ValueError,UnicodeDecodeError):
                return self.send({'error':'Invalid login request.'},400)
            address=self.client_address[0]
            if address in ('127.0.0.1','::1'):address=self.headers.get('X-Real-IP',address)
            token,limited=AUTH.login(username,password,address)
            if not token:return self.login_page(429 if limited else 401,limited)
            return self.send('',303,headers={'Location':'/','Set-Cookie':self.session_cookie(token)})
        if not self.require_login():return
        if endpoint=='/logout':
            AUTH.logout(self.session_token())
            return self.send('',303,headers={'Location':'/login','Set-Cookie':self.session_cookie('',True)})
        if endpoint not in ('/api/sync','/api/ifb/sync'):
            return self.send({'error': 'Page not found.'}, 404)
        if endpoint=='/api/ifb/sync':
            if self.headers.get('X-TSE-Request') != 'sync' or (self.headers.get('Origin') and urlsplit(self.headers['Origin']).netloc != self.headers.get('Host')):
                return self.send({'error': 'Refresh must be started from this app.'},403)
            with SYNC_LOCK:
                if IFB_SYNC_PROCESS is not None and IFB_SYNC_PROCESS.poll() is None:
                    return self.send({'started':False,'message':'An IFB refresh is already running.'},202)
                with (ifb_archive.FOLDER/'sync.log').open('a') as log:
                    IFB_SYNC_PROCESS=subprocess.Popen([sys.executable,str(ROOT/'scripts/ifb_archive.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            return self.send({'started':True,'message':'IFB archive refresh started.'},202)
        if urlsplit(self.path).path != '/api/sync':
            return self.send({'error': 'Page not found.'}, 404)
        # Require same-origin mutation requests and the UI header in addition to login.
        origin = self.headers.get('Origin')
        if self.headers.get('X-TSE-Request') != 'sync' or (origin and urlsplit(origin).netloc != self.headers.get('Host')):
            return self.send({'error': 'Refresh must be started from this app.'}, 403)
        with SYNC_LOCK:
            if SYNC_PROCESS is not None and SYNC_PROCESS.poll() is None:
                return self.send({'started': False, 'message': 'An archive refresh is already running.'}, 202)
            log = (ROOT/'data/sync.log').open('a')
            SYNC_PROCESS = subprocess.Popen([sys.executable, str(ROOT/'scripts/sync_archive.py')], cwd=ROOT,
                                             stdout=log, stderr=subprocess.STDOUT)
            log.close()
        return self.send({'started': True, 'message': 'Archive refresh started.'}, 202)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--no-index-watch', action='store_true')
    args = parser.parse_args()
    global AUTH
    auth_path=os.environ.get('TSE_AUTH_FILE',str(ROOT/'data/auth.json'))
    try:AUTH=SingleUserAuth.load(auth_path)
    except (OSError,ValueError,KeyError) as error:
        parser.exit(2,f'Configure login with python3 scripts/configure_login.py before starting: {error}\n')
    init_db()
    ifb_archive.init_db()
    indexer = None
    if not args.no_index_watch:
        log = (ROOT/'data/index.log').open('a')
        indexer = subprocess.Popen([sys.executable, str(ROOT/'scripts/index_reports.py'), '--watch'], cwd=ROOT,
                                   stdout=log, stderr=subprocess.STDOUT)
        log.close()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    print(f'TSE Market Archive: http://{args.host}:{args.port} (login required)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if indexer and indexer.poll() is None:
            indexer.terminate()
            indexer.wait(timeout=10)


if __name__ == '__main__':
    main()
