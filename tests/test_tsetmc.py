"""Dated TSETMC values, source selection, unit conversion, and whole-view fund exclusion."""
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import tsetmc_daily as feed
import index_reports as index
import app


def item(code='100',symbol='سهم1',fund=0):
    return {'instrument_code':code,'symbol':symbol,'display_symbol':symbol[:-1],'company':'Example',
            'market':'tse','is_fund':fund,'security_type':305 if fund else 300,'isin':'IRO1TEST0001'}


def sample(instrument=None):
    i=instrument or item()
    client={'clientType':{'recDate':20261114,'insCode':i['instrument_code'],'buy_I_Value':100,'buy_N_Value':50,
        'sell_I_Value':40,'sell_N_Value':110,'buy_I_Volume':10,'buy_N_Volume':5,'sell_I_Volume':4,'sell_N_Volume':11,
        'buy_I_Count':2,'buy_N_Count':1,'sell_I_Count':3,'sell_N_Count':1}}
    closing={'closingPriceDaily':{'dEven':20261114,'insCode':i['instrument_code'],'qTotCap':150,'qTotTran5J':15,
        'pClosing':11,'pDrCotVal':12}}
    return i,client,closing


class TsetmcTests(unittest.TestCase):
    def test_dates_actual_values_and_units(self):
        self.assertEqual(feed.jalali(date(2026,11,14)),'1405/08/23')
        self.assertEqual(feed.jalali(date(2026,11,15)),'1405/08/24')
        r=feed.observation(*sample(),date(2026,11,14))
        self.assertEqual(r['retail_net_rial'],60)
        self.assertEqual(r['net_retail_flow_billion_toman'],Decimal('0.000000006'))
        self.assertEqual(r['closing_price_rial'],11)
        # Volume delta × closing price = 66, which must not replace actual net value 60.
        self.assertNotEqual(r['retail_net_rial'],r['retail_net_volume']*r['closing_price_rial'])

    def test_missing_values_dates_identity_and_accounting_rejected(self):
        for change in ['value','date','identity','volume','zero_turnover']:
            i,c,p=sample()
            if change=='value':c['clientType'].pop('buy_I_Value')
            if change=='date':c['clientType']['recDate']=20261113
            if change=='identity':p['closingPriceDaily']['insCode']='999'
            if change=='volume':p['closingPriceDaily']['qTotTran5J']=14
            if change=='zero_turnover':p['closingPriceDaily']['qTotCap']=0
            with self.subTest(change=change),self.assertRaises(ValueError):feed.observation(i,c,p,date(2026,11,14))

    def test_zero_trade_requires_dated_identity(self):
        i,c,p=sample();p['closingPriceDaily'].update(qTotCap=0,qTotTran5J=0)
        self.assertIsNone(feed.observation(i,{},p,date(2026,11,14)))
        p['closingPriceDaily']['dEven']=20261113
        with self.assertRaises(ValueError):feed.observation(i,{},p,date(2026,11,14))

    def test_universe_separates_markets_and_omits_secondary_boards(self):
        def row(code,flow,yval,isin='IRO1TEST0001'):
            return {'insCode':code,'flow':flow,'yVal':yval,'insID':isin,'lva':'سهم','lvc':'شرکت'}
        universe=feed.instruments({'marketwatch':[row('1',1,300),row('2',4,309),row('3',2,305),row('4',1,300,'IRO1TEST0003'),row('5',3,311)]})
        self.assertEqual([r['instrument_code'] for r in universe],['1','2','3'])
        self.assertEqual([r['market'] for r in universe],['tse','ifb','ifb'])
        self.assertTrue(universe[-1]['is_fund'])

    def test_api_revisions_keep_archive_and_fund_filter_changes_all_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);db_path=root/'data/archive.sqlite3';index.init_db(db_path)
            with index.connect(db_path) as db:
                daily={'date':'1405/08/23','file':'old.xlsx','symbols':1,'turnover_rial':'100','retail_net_rial':'10'}
                db.execute('''INSERT INTO workbooks(sha,file,date,state,daily) VALUES ('excel','data/raw/old.xlsx','1405/08/23','ready',?)''',(json.dumps(daily),))
            stock=feed.observation(*sample(),date(2026,11,14))
            fund=feed.observation(*sample(item('200','پالایش1',1)),date(2026,11,14))
            # An unnamed historical fund can be excluded by authoritative alias metadata.
            fund['company']='پالایشی یکم'
            with patch.object(feed,'ROOT',root):
                self.assertTrue(feed.publish('tse',date(2026,11,14),[stock,fund],[],2,0))
                self.assertTrue(feed.publish('tse',date(2026,11,14),[stock,fund],[],2,0))
                self.assertFalse(feed.publish('tse',date(2026,11,14),[stock],[],2,0,limited=True))
                self.assertFalse(feed.publish('tse',date(2026,11,14),[stock],[],2,0))
                failures=[{'symbol':str(n),'reason':'Accounting mismatch'} for n in range(3)]
                self.assertFalse(feed.publish('tse',date(2026,11,14),[stock],failures,20,0))
            with index.connect(db_path) as db,patch.object(app,'status',return_value={}):
                self.assertEqual(db.execute('SELECT COUNT(*) FROM workbooks').fetchone()[0],2)
                self.assertEqual(db.execute('SELECT source FROM active_reports').fetchone()[0],'tsetmc')
                query={'window':'all','exclude_funds':'1'}
                overview=app.overview(db,query)
                self.assertEqual(overview['days'][0]['symbols'],1)
                self.assertEqual(overview['aggregate']['net_rial'],60)
                self.assertEqual(app.flow_query(db,query)['total'],1)
                self.assertEqual(app.flow_query(db,query),app.flow_query(db,query,export=True))
                self.assertEqual(app.symbol_detail(db,{**query,'symbol':'پالایش1'})['days'],[])
                self.assertEqual(app.overview(db,{'window':'all'})['days'][0]['symbols'],2)
                # Exact classification also catches archive rows whose name lacks صندوق.
                db.execute('UPDATE flows SET is_fund=NULL')
                db.execute("INSERT INTO instrument_classification VALUES ('پالایش1','200',1,305,'now')")
                self.assertEqual(app.flow_query(db,query)['total'],1)


if __name__=='__main__':unittest.main()
