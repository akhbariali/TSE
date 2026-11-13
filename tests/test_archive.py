"""Regression checks for archive deduplication, date parsing, and scoped queries."""
import contextlib
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
sys.path.insert(0, str(ROOT))
import download_reports as download
from analyze_reports import analyze, report_date, summary_values
import app
import index_reports as index


def payload(text):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as archive:
        archive.writestr('xl/workbook.xml', '<workbook>'+text+'</workbook>')
    return out.getvalue()


def item(report_id, file_id, name='report.xlsx', date='2026-11-10T00:00:00'):
    return {'title': f'Report {report_id}', 'effectiveFrom': date,
            'content': {'id': report_id, 'publishAt': date, 'files': [
                {'fileId': file_id, 'fileName': name}]}}


class DownloaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(download, 'ROOT', self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temp.cleanup()

    def test_all_pages_deduplicate_and_resume_without_fetching_files(self):
        a, b = item(1,'a'), item(2,'b',date='2026-11-09T00:00:00')
        c = item(3,'c',date='2026-11-08T00:00:00')
        data = payload('same'), payload('revision')
        calls = []
        def get(url):
            calls.append(url)
            if '/List/' in url:
                page = int(download.urllib.parse.parse_qs(download.urllib.parse.urlsplit(url).query)['PageNumber'][0])
                return json.dumps({'totalPages':2,'totalCount':3,'items':[a,b] if page==1 else [a,c]}).encode()
            return data[1] if url.endswith('/c') else data[0]
        with patch.object(download,'get',side_effect=get), contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(download.Downloader().run())
            manifest=json.loads((self.root/'data/download-manifest.json').read_text())
            self.assertEqual(len(manifest),3)
            self.assertEqual(len(list((self.root/'data/raw').glob('*.xlsx'))),2)
            self.assertEqual(len({r['sha256'] for r in manifest}),2)
            self.assertTrue(any('--' in r['file'] for r in manifest))
            calls.clear()
            self.assertTrue(download.Downloader().run())
            self.assertTrue(all('/List/' in u for u in calls))
            self.assertEqual(len(json.loads((self.root/'data/download-manifest.json').read_text())),3)
            # A limited run must not truncate the previously complete manifest.
            self.assertTrue(download.Downloader(limit=1).run())
            self.assertEqual(len(json.loads((self.root/'data/download-manifest.json').read_text())),3)

    def test_failed_attachment_retains_success_and_is_retried(self):
        a,b=item(1,'a','a.xlsx'),item(2,'b','b.xlsx')
        failed=True
        def get(url):
            if '/List/' in url:
                return json.dumps({'totalPages':1,'totalCount':2,'items':[a,b]}).encode()
            if url.endswith('/b') and failed:
                raise OSError('temporary network failure')
            return payload(url)
        with patch.object(download,'get',side_effect=get),contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(download.Downloader().run())
            self.assertEqual(len(json.loads((self.root/'data/download-manifest.json').read_text())),1)
            failed=False
            self.assertTrue(download.Downloader().run())
            self.assertEqual(len(json.loads((self.root/'data/download-manifest.json').read_text())),2)
            self.assertEqual(json.loads((self.root/'data/download-errors.json').read_text()),[])

    def test_corrupt_existing_file_is_downloaded_again(self):
        a=item(1,'a')
        calls=[]
        def get(url):
            calls.append(url)
            if '/List/' in url:
                return json.dumps({'totalPages':1,'totalCount':1,'items':[a]}).encode()
            return payload('valid')
        with patch.object(download,'get',side_effect=get),contextlib.redirect_stdout(io.StringIO()):
            download.Downloader().run()
            manifest=json.loads((self.root/'data/download-manifest.json').read_text())
            (self.root/manifest[0]['file']).write_bytes(b'corrupt')
            calls.clear()
            download.Downloader().run()
            self.assertTrue(any('/File/Download/' in u for u in calls))
            current=json.loads((self.root/'data/download-manifest.json').read_text())[0]
            self.assertEqual(hashlib.sha256((self.root/current['file']).read_bytes()).hexdigest(),current['sha256'])


class ParsingTests(unittest.TestCase):
    def test_dates_across_historical_layouts(self):
        for value in ['1405/08/19','1405-08-19','14050819','۱۴۰۵/۰۸/۱۹']:
            self.assertEqual(report_date({7:{'D':'مورخ','F':value}},Path('KH.xlsx')),'1405/08/19')
        with self.assertRaises(ValueError):
            report_date({7:{'D':'مورخ'}},Path('unknown.xlsx'))

    def test_shifted_summary_and_missing_share_are_not_fabricated(self):
        rows={14:{'D':'حجم كل معاملات','F':'ارزش كل معاملات'},15:{'D':'12','F':'120'}}
        self.assertEqual(summary_values(rows),(Decimal(12),Decimal(120),None,None))

    def test_partial_rows_and_shifted_columns(self):
        def sheet(rows, shifted=False):
            headers={3:{'A':'ردیف','B':'نماد','C':'نام شركت','D':'ارزش خرید مقدار','F':'ارزش خرید درصد','H':'ارزش فروش مقدار','J':'ارزش فروش درصد'},
                     4:{'D':'حقيقي','E':'حقوقي','H':'حقيقي','I':'حقوقي'}}
            for n,(symbol,values) in enumerate(rows,5):
                headers[n]={'A':str(n-4),'B':symbol,'C':'Company',**dict(zip(['D','E','H','I'],values))}
            if shifted:
                headers={n:{chr(ord(c)+1):v for c,v in row.items()} for n,row in headers.items()}
            return headers
        values=sheet([('good',['100','200','150','150']),('bad',['100','20','10','10']),
                      ('no-volume',['80','20','50','50']),('copied',['10','20','15','15'])],True)
        volumes=sheet([('good',['10','20','15','15']),('bad',['10','2','1','11']),
                       ('copied',['10','20','15','15'])])
        sheets={'خلاصه بازار':{7:{'F':'1405/03/19'},10:{'D':'حجم كل معاملات','F':'ارزش كل معاملات'},11:{'D':'100','F':'1000'}},
                'تغییر مالکیت براساس ارزش':values,'تغییر مالکیت براساس حجم':volumes}
        with patch('analyze_reports.workbook',return_value=sheets):
            day,records,issues=analyze(Path('test.xlsx'))
        by_symbol={r['symbol']:r for r in records}
        self.assertEqual(set(by_symbol),{'good','no-volume'})
        self.assertEqual(day['turnover_rial'],400)
        self.assertEqual(day['volume'],30)
        self.assertTrue(day['partial'])
        self.assertIsNone(by_symbol['no-volume']['volume'])
        self.assertEqual(by_symbol['no-volume']['retail_buy_vwap_rial'],'')
        self.assertEqual(len(day['excluded_rows']),2)
        self.assertTrue(issues)

    def test_known_workbook_reconciles_with_verified_figures(self):
        source=ROOT/'KH - 14050819.xlsx'
        if not source.exists():self.skipTest('Source fixture is not available')
        day,records,issues=analyze(source)
        self.assertEqual(day['date'],'1405/08/19')
        self.assertEqual(len(records),1192)
        self.assertEqual(day['turnover_rial'],Decimal('596948215456567'))
        self.assertEqual(day['retail_net_rial'],Decimal('74101817413833'))
        self.assertEqual(issues,[])


class RecoveryIndexTests(unittest.TestCase):
    def test_partial_reports_enter_analysis_and_validated_revision_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'archive.sqlite3'
            original_connect=index.connect
            with patch.object(index,'DB',path), patch.object(index,'connect',lambda: original_connect(path)):
                index.init_db()
                with index.connect() as db:
                    db.executemany('INSERT INTO workbooks (sha,file,date,state,published_at,report_id) VALUES (?,?,?,?,?,?)',[
                        ('old','old.xlsx','1405/03/19','ready','2026-06-10',1),
                        ('new','new.xlsx','1405/03/19','partial','2026-06-11',2),
                        ('partial','partial.xlsx','1405/03/20','partial','2026-06-12',3),
                        ('bad','bad.xlsx','1405/03/21','unsupported','2026-06-13',4)])
                    self.assertEqual([r['sha'] for r in db.execute('SELECT sha FROM active_reports ORDER BY date')],['old','partial'])
                index.init_db()  # Existing databases also migrate idempotently.


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row
        self.db.executescript('''CREATE TABLE active_reports (sha,date,daily,published_at,report_id,state);
          CREATE TABLE flows(workbook_sha,symbol,company,search_text,turnover_rial,retail_net_rial,
                             retail_buy_rial,retail_sell_rial,volume REAL);''')
        for n in range(1,4):
            self.db.execute('INSERT INTO active_reports VALUES (?,?,?,?,?,?)',(str(n),f'1405/08/{n:02}', '{}','2026-11-10',n,'ready'))
            self.db.execute('INSERT INTO flows VALUES (?,?,?,?,?,?,?,?,?)',(str(n),'وبملت1','بانک ملت','وبملت1بانکملت',100,n*10,50+n*10,50,n*10))

    def tearDown(self):self.db.close()

    def test_window_scopes_rankings_and_exports_identically(self):
        result=app.flow_query(self.db,{'window':'2'})
        self.assertEqual(result['scope']['reports'],2)
        self.assertEqual(result['items'][0]['net_rial'],50)
        self.assertEqual(result['items'][0]['observed_days'],2)
        self.assertEqual(result,app.flow_query(self.db,{'window':'2'},export=True))
        result=app.flow_query(self.db,{'start':'1405/08/01','end':'1405/08/01'})
        self.assertEqual(result['items'][0]['net_rial'],10)

    def test_average_price_is_volume_weighted_and_missing_without_volume(self):
        result=app.flow_query(self.db,{'window':'2'})
        self.assertAlmostEqual(result['items'][0]['average_price_rial'],200/50)
        detail=app.symbol_detail(self.db,{'window':'all','symbol':'وبملت1'})
        self.assertEqual(detail['days'][0]['average_price_rial'],10)
        self.db.execute("UPDATE flows SET volume=NULL WHERE workbook_sha='1'")
        self.assertEqual(app.flow_query(self.db,{'window':'all'})['items'][0]['average_price_rial'],4)
        self.db.execute('UPDATE flows SET volume=0')
        self.assertIsNone(app.flow_query(self.db,{'window':'all'})['items'][0]['average_price_rial'])
        self.assertIsNone(app.symbol_detail(self.db,{'window':'all','symbol':'وبملت1'})['days'][0]['average_price_rial'])

    def test_search_is_literal_and_normalizes_persian_variants(self):
        self.assertEqual(app.flow_query(self.db,{'window':'all','q':'بانك ملت'})['total'],1)
        self.assertEqual(app.flow_query(self.db,{'window':'all','q':"' OR 1=1 --"})['total'],0)

    def test_invalid_ranges_and_nonfinite_thresholds_are_rejected(self):
        with self.assertRaises(ValueError):app.selection(self.db,{'start':'14050819'})
        with self.assertRaises(ValueError):app.selection(self.db,{'start':'1405/08/19','end':'1405/08/01'})
        with self.assertRaises(ValueError):app.flow_query(self.db,{'minimum':'nan'})


if __name__=='__main__':unittest.main()
