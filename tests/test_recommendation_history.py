"""Dated signal lists must match rankings and never borrow future observations."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import app
from test_retail_signals import history
import index_reports as index


class HistoryTests(unittest.TestCase):
    def test_retail_history_matches_daily_list_and_keeps_missing_outcomes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'archive.sqlite3';index.init_db(path)
            with index.connect(path) as db:
                db.execute("INSERT INTO instrument_classification VALUES ('stock1','100',0,300,'now')")
                for n,row in enumerate(history()):
                    db.execute('INSERT INTO workbooks(sha,file,date,state) VALUES (?,?,?,?)',(str(n),str(n),row['date'],'ready'))
                    db.execute('INSERT INTO flows(workbook_sha,symbol,company,search_text,turnover_rial,volume,retail_net_rial) VALUES (?,?,?,?,?,?,?)',
                        (str(n),'stock1','Stock','stock',1000,10,row['retail_net_rial']))
                with patch.object(app,'MODEL_DB',Path(folder)/'absent'):
                    result=app.recommendation_history(db,{'window':'5','symbol':'stock1'})
                self.assertEqual(len(result['retail']),1)
                signal=result['retail'][0]
                current=app.recommendations(db,{'window':'5'})['items'][0]
                self.assertEqual(signal['score'],current['score']);self.assertEqual(signal['rank'],1)
                self.assertIsNone(signal['next_return']);self.assertIsNone(signal['next_date'])
                earlier=app.recommendation_history(db,{'window':'all','end':'1405/08/24','symbol':'stock1'})
                self.assertEqual(earlier['retail'],[])

    def test_model_market_fund_ranking_date_and_history_filters(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'archive.sqlite3';index.init_db(path)
            scores=Path(folder)/'model.sqlite3'
            with sqlite3.connect(scores) as model:
                model.execute('CREATE TABLE metadata(payload TEXT)')
                model.execute('INSERT INTO metadata VALUES (?)',(json.dumps({'data_through':'1405/08/25','target_kind':'stock_net_positive_v1'}),))
                model.execute('CREATE TABLE scores(market TEXT,date TEXT,symbol TEXT,is_fund INTEGER,probability REAL)')
                for market in ['tse','ifb']:
                    for i in range(60):
                        model.execute('INSERT INTO scores VALUES (?,?,?,?,?)',(market,'1405/08/25',f's{i:02}',int(i==0),1-i*.01))
            with index.connect(path) as db,patch.object(app,'MODEL_DB',scores):
                db.execute("INSERT INTO workbooks(sha,file,date,state) VALUES ('a','a','1405/08/25','ready')")
                result=app.model_recommendations(db,{'window':'all','exclude_funds':'1'})
                self.assertEqual(len(result['items']),50)
                self.assertEqual(result['items'][0]['symbol'],'s01')
                self.assertEqual({r['market'] for r in result['items']},{'tse'})
                self.assertEqual(app.model_recommendations(db,{'window':'all','symbol':'s55'},True)['items'],[])
                signal=app.model_recommendations(db,{'window':'all','symbol':'s05','_market':'ifb'},True)['items']
                self.assertEqual(len(signal),1);self.assertEqual(signal[0]['rank'],6)
                expanded=app.model_recommendations(db,{'window':'all','symbol':'s45'},True)['items']
                self.assertEqual(expanded[0]['rank'],46)
                db.execute("INSERT INTO workbooks(sha,file,date,state) VALUES ('b','b','1405/08/26','ready')")
                stale=app.model_recommendations(db,{'window':'all'})
                self.assertEqual(stale['items'],[]);self.assertTrue(stale['stale'])


if __name__=='__main__':unittest.main()
