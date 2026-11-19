"""Full-history CSV preserves revisions, markets, source precision and old files on failure."""
import csv
import fcntl
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import export_market_csv as export
import index_reports as index


class ExportTests(unittest.TestCase):
    def seed(self,root):
        for market,relative in [('tse','data/archive.sqlite3'),('ifb','data/ifb/archive.sqlite3')]:
            db_path=root/relative;index.init_db(db_path)
            with index.connect(db_path) as db:
                for sha,source,value in [('old','excel',10),('current','tsetmc',20)]:
                    record={'symbol':'Fund1','company':'صندوق Example','market':market,'retail_buy_rial':'9007199254740993',
                            'retail_sell_rial':'9007199254740973','retail_net_rial':value,'volume':'2','turnover_rial':'30',
                            'buy_I_Count':'3','is_fund':1}
                    path=root/f'data/{market}-{sha}.json'
                    path.write_text(json.dumps({'date':'1405/08/27','market':market,'records':[record]}))
                    db.execute('INSERT INTO workbooks(sha,file,date,state,source) VALUES (?,?,?,?,?)',(sha,str(path.relative_to(root)),'1405/08/27','ready',source))
                    db.execute('INSERT INTO flows(workbook_sha,symbol,company,search_text,turnover_rial,volume,retail_net_rial) VALUES (?,?,?,?,?,?,?)',
                               (sha,'Fund1','صندوق Example','fund',30,2,value))

    def test_all_markets_funds_exact_source_and_no_duplicate_revisions(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.seed(root)
            result=export.export_all(root);path=Path(result['file'])
            with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            self.assertEqual(result['rows'],{'tse':1,'ifb':1})
            self.assertEqual([r['market'] for r in rows],['tse','ifb'])
            self.assertEqual(rows[0]['retail_buy_rial'],'9007199254740993')
            self.assertEqual(rows[0]['retail_buy_count'],'3');self.assertEqual(rows[0]['is_fund'],'1')
            self.assertNotIn('score',rows[0]);self.assertEqual(rows[0]['source_sha'],'current')
            path.write_text('previous')
            export.export_all(root)
            self.assertFalse(list(path.parent.glob('*.tmp')))
            self.assertTrue(path.read_bytes().startswith(b'\xef\xbb\xbf'))

    def test_failed_export_preserves_previous_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.seed(root)
            path=Path(export.export_all(root)['file']);before=path.read_bytes()
            (root/'data/ifb-current.json').unlink()
            with self.assertRaises(FileNotFoundError):export.export_all(root)
            self.assertEqual(path.read_bytes(),before)
            self.assertFalse(list(path.parent.glob('*.tmp')))

    def test_export_reads_committed_records_during_collection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.seed(root);folder=root/'data/tsetmc';folder.mkdir()
            with (folder/'sync.lock').open('w') as handle:
                fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
                self.assertEqual(export.export_all(root)['rows'],{'tse':1,'ifb':1})


if __name__=='__main__':unittest.main()
