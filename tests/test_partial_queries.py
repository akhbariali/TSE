"""Checked rows can be used without promoting partial tables to market totals."""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import app
import index_reports as index


class PartialQueries(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'archive.sqlite3'
        original=index.connect
        with patch.object(index,'DB',self.path), patch.object(index,'connect',side_effect=lambda:original(self.path)):
            index.init_db()
            # Repeating initialization must preserve existing data and views.
            index.init_db()
        self.db=original(self.path)
        self.add_report('full','1405/08/01',True,1)
        self.add_report('partial','1405/08/02',False,1)
        self.add_report('fields','1405/08/03',False,0)
        for sha,net in [('full',10),('partial',20),('fields',None)]:
            self.db.execute('''INSERT INTO flows
                (workbook_sha,symbol,company,search_text,turnover_rial,retail_net_rial,retail_buy_rial,retail_sell_rial,source_data)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (sha,'AAA','Alpha','aaa',100 if net is not None else None,net,60,50,
                 json.dumps({'value_valid':net is not None,'volume_valid':False,'issues':['volume absent']})))

    def add_report(self,sha,date,complete,usable):
        daily={'date':date,'validation_issues':1,'quality':{'market_eligible':complete,
               'symbol_eligible':bool(usable),'value':{'usable_rows':usable}}}
        self.db.execute('''INSERT INTO workbooks
            (sha,file,date,state,daily,published_at,report_id) VALUES (?,?,?,?,?,?,?)''',
            (sha,sha+'.xlsx',date,'warning',json.dumps(daily),'2026-11-11',1))

    def tearDown(self):
        self.db.close();self.temp.cleanup()

    def test_summary_warning_does_not_block_complete_detail(self):
        market=[r['sha'] for r in self.db.execute('SELECT sha FROM active_reports')]
        symbols=[r['sha'] for r in self.db.execute('SELECT sha FROM symbol_reports ORDER BY date')]
        self.assertEqual(market,['full'])
        self.assertEqual(symbols,['full','partial'])

    def test_partial_rows_enter_symbol_queries_and_matching_export(self):
        query={'window':'all'}
        result=app.flow_query(self.db,query)
        self.assertEqual(result,app.flow_query(self.db,query,export=True))
        self.assertEqual(result['items'][0]['net_rial'],30)
        self.assertEqual(result['items'][0]['observed_days'],2)
        self.assertEqual(result['scope']['partial_reports'],1)
        self.assertEqual(result['scope']['reports_with_warnings'],2)

    def test_invalid_value_row_never_enters_symbol_history(self):
        self.db.execute("INSERT INTO flows(workbook_sha,symbol,company,search_text,retail_buy_rial) VALUES ('partial','BAD','Bad','bad',100)")
        self.assertEqual(app.flow_query(self.db,{'window':'all','q':'bad'})['total'],0)
        self.assertEqual(app.symbol_detail(self.db,{'window':'all','symbol':'BAD'})['days'],[])
        self.assertEqual(app.report_records(self.db,'partial')[1]['retail_net_rial'],None)

    def test_one_revision_per_date_prefers_complete_over_partial(self):
        self.add_report('newerpartial','1405/08/01',False,10)
        self.db.execute("UPDATE workbooks SET published_at='2026-11-12' WHERE sha='newerpartial'")
        selected=[r['sha'] for r in self.db.execute("SELECT sha FROM symbol_reports WHERE date='1405/08/01'")]
        self.assertEqual(selected,['full'])

    def test_unavailable_numeric_values_remain_null_in_source_export(self):
        records=app.report_records(self.db,'fields')
        self.assertIsNone(records[0]['retail_net_rial'])
        self.assertFalse(records[0]['value_valid'])
        self.assertIn('volume absent',records[0]['issues'])


if __name__=='__main__':unittest.main()
