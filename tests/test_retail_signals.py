"""Research rules must respond to buying strength, not raw trade size."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import retail_signals
import app
import index_reports as index


def history(recent=None,scale=1):
    ratios=[-.02,.01,0,.02,-.01]*4+(recent or [.25,.30,.25,.35,.30])
    return [{'date':f'1405/08/{i+1:02}', 'retail_net_rial':r*1000*scale,
             'turnover_rial':1000*scale,'source':'excel','report_state':'ready'} for i,r in enumerate(ratios)]


class SignalTests(unittest.TestCase):
    def test_sustained_buying_is_independent_of_absolute_volume(self):
        a=retail_signals.assess(history(),'1405/08/25')
        b=retail_signals.assess(history(scale=10000),'1405/08/25')
        self.assertTrue(a['recommended']);self.assertEqual(a['score'],b['score'])
        self.assertEqual(a['buying_days'],5);self.assertEqual(a['baseline_observations'],20)
        self.assertIn('Sustained buying',a['reasons'][0])

    def test_spike_stale_short_history_and_normal_large_trades(self):
        self.assertTrue(retail_signals.assess(history([0,0,0,0,.5]),'1405/08/25')['recommended'])
        self.assertFalse(retail_signals.assess(history([0,.01,0,.02,0],scale=1e10),'1405/08/25')['recommended'])
        self.assertFalse(retail_signals.assess(history()[:24],'1405/08/24')['eligible'])
        self.assertFalse(retail_signals.assess(history(),'1405/08/26')['eligible'])
        self.assertFalse(retail_signals.assess(history([-.5]*5),'1405/08/25')['recommended'])

    def test_baseline_excludes_recent_and_reports_source_changes(self):
        data=history();data[-1].update(source='tsetmc',report_state='partial')
        result=retail_signals.assess(data,'1405/08/25')
        self.assertEqual(result['baseline_ratio'],0)
        self.assertTrue(result['mixed_sources']);self.assertEqual(result['partial_reports'],1)
        self.assertLess(result['score'],100)  # Flat baselines use a finite dispersion floor.

    def test_query_as_of_fund_exclusion_and_context_outside_visible_window(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'archive.sqlite3';index.init_db(path)
            with index.connect(path) as db:
                db.execute("INSERT INTO instrument_classification VALUES ('stock1','100',0,300,'now')")
                db.execute("INSERT INTO instrument_classification VALUES ('fund1','200',1,305,'now')")
                for n,row in enumerate(history()):
                    sha=str(n);daily={'date':row['date'],'file':sha,'symbols':2,'turnover_rial':2000,'retail_net_rial':row['retail_net_rial']*2}
                    db.execute('INSERT INTO workbooks(sha,file,date,state,daily) VALUES (?,?,?,?,?)',(sha,sha,row['date'],'ready',json.dumps(daily)))
                    for symbol,fund in [('stock1',0),('fund1',1)]:
                        db.execute('INSERT INTO flows(workbook_sha,symbol,company,search_text,turnover_rial,retail_net_rial,is_fund) VALUES (?,?,?,?,?,?,?)',
                            (sha,symbol,'Example','example',1000,row['retail_net_rial'],fund))
                q={'window':'5','exclude_funds':'1'}
                result=app.recommendations(db,q)
                self.assertEqual([r['symbol'] for r in result['items']],['stock1'])
                self.assertEqual(result['context_reports'],25)
                self.assertEqual(len(app.recommendations(db,{'window':'5'})['items']),2)
                # A date in the past must not see subsequent observations.
                earlier=app.recommendations(db,{'window':'all','end':'1405/08/24'})
                self.assertEqual(earlier['as_of'],'1405/08/24');self.assertEqual(earlier['assessed'],0)


if __name__=='__main__':unittest.main()
