"""IFB layout, dates, partial recovery, pagination, and market isolation."""
from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import ifb_archive as ifb
import app


def ownership():
    return {7:{'B':'14050819'},8:{'B':'14050819'},11:{'B':'14050819','D':'14050819'},
        14:{'E':'خريد','M':'فروش','U':'كل'},
        15:{'E':'حقوقي','I':'حقيقي','M':'حقوقي','Q':'حقيقي','U':'خريداران','Y':'فروشندگان'},
        16:{'A':'نام بازار','B':'نام زيرگروه بازار','C':'نام شرکت','D':'کد فارسي نماد',
            **{c:label for start in [4,8,12,16,20,24] for c,label in zip([chr(65+start+i) if start+i<26 else 'A'+chr(65+start+i-26) for i in range(4)],['تعداد نفرات','تعداد دفعات','حجم','ارزش'])}},
        17:{'A':'بازار اول','B':'عادي','C':'Example','D':'مثال1','G':'10','H':'100','K':'20','L':'200','O':'15','P':'150','S':'15','T':'150','W':'30','X':'300','AA':'30','AB':'300'},
        18:{'C':'Second','D':'دوم1','K':'5','L':'50','S':'5','T':'50','W':'5','X':'50','AA':'5','AB':'50'},
        19:{'A':'جمع كل','C':'999','D':'350'}}


def prices():
    return {7:{'B':'14050818'},8:{'B':'14050819'},11:{'B':'14050819','D':'14050819'},
        14:{'A':'نام بازار','B':'نام زيرگروه بازار','C':'نام شرکت','D':'کد فارسي نماد',
            'F':'حجم معاملات','G':'ارزش معاملات','K':'قیمت آخرین معامله','M':'قيمت ميانگين','N':'قیمت پایانی انتهای بازه'},
        15:{'A':'بازار اول','B':'عادي','C':'Example','D':'مثال1','F':'30','G':'300','K':'11','M':'8','N':'10'}}


class IFBTests(unittest.TestCase):
    def parse(self,rows,name='حقيقي و حقوقي'):
        with patch.object(ifb,'workbook',return_value={name:rows}):
            return ifb.parse(Path('sample.xlsx'))

    def test_flow_groups_blanks_merged_labels_and_totals(self):
        kind,date,records,issues=self.parse(ownership())
        self.assertEqual((kind,date,len(records)),('flows','1405/08/19',2))
        self.assertEqual(records[0]['retail_net_rial'],50)
        self.assertEqual(records[1]['institutional_buy_rial'],0)
        self.assertEqual(records[1]['market'],'بازار اول')
        self.assertEqual(records[1]['submarket'],'عادي')
        self.assertEqual(issues,[])

    def test_bad_value_excluded_bad_volume_retains_value(self):
        rows=ownership();rows[17]['T']='999';rows[18]['S']='3'
        _,_,records,issues=self.parse(rows)
        self.assertEqual([r['symbol'] for r in records],['دوم1'])
        self.assertIsNone(records[0]['volume'])
        self.assertIsNone(records[0]['retail_buy_vwap_rial'])
        self.assertTrue(any('Excluded مثال1' in issue for issue in issues))

    def test_price_date_is_report_end_and_average_is_calculated(self):
        _,day,records,_=self.parse(prices(),'قيمت و تغيير‌قيمت')
        self.assertEqual(day,'1405/08/19')
        self.assertEqual(records[0]['average_price_rial'],10)
        self.assertEqual(records[0]['source_average_price_rial'],8)
        self.assertEqual(records[0]['closing_price_rial'],10)

    def test_multiday_flows_are_not_daily_observations(self):
        rows=ownership();rows[7]['B']='14050818'
        with self.assertRaisesRegex(ValueError,'Multi-day'):self.parse(rows)

    def test_price_references_do_not_duplicate_flows_or_cross_markets(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);folder=root/'data/ifb';path=root/'sample.xlsx';path.write_bytes(b'flow sample')
            with patch.object(ifb,'ROOT',root),patch.object(ifb,'FOLDER',folder),patch.object(ifb,'DB',folder/'archive.sqlite3'):
                with patch.object(ifb,'workbook',return_value={'حقيقي و حقوقي':ownership()}):ifb.ingest(path,1)
                path.write_bytes(b'price sample')
                with patch.object(ifb,'workbook',return_value={'قيمت و تغيير‌قيمت':prices()}):ifb.ingest(path,2)
                with ifb.connect(ifb.DB) as db:
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM active_reports').fetchone()[0],1)
                    result=app.symbol_detail(db,{'symbol':'مثال1','_market':'ifb','window':'all'})
                    self.assertEqual(len(result['days']),1)
                    self.assertEqual(result['days'][0]['closing_price_rial'],10)
                    self.assertEqual(result['days'][0]['average_price_rial'],10)
                tse=root/'data/archive.sqlite3';ifb.base_init(tse)
                with ifb.connect(tse) as db:
                    self.assertEqual(app.flow_query(db,{'window':'all'})['total'],0)

    def test_listing_extracts_only_visible_daily_excel_links_and_pages(self):
        listing=ifb.Listing();listing.feed('''<input type="hidden" name="__VIEWSTATE" value="token"><table id="ContentPlaceHolder1_grdPRs">
          <tr><td>1</td><td>آمار معاملات</td><td>روزانه</td><td>1405/08/19</td><td>نماد</td><td>1405/08/20</td><td>قیمت</td><td>
          <a href="/GetFiles/GetPeriodicalFile.aspx?id=1&amp;type=Excel">Excel</a></td></tr>
          <tr><td>2</td><td>آمار</td><td>ماهانه</td><td>1405/08/19</td><td>نماد</td><td></td><td>قیمت</td><td>
          <a href="/GetFiles/GetPeriodicalFile.aspx?id=2&amp;type=Excel">Excel</a></td></tr>
          <tr><td><a href="javascript:__doPostBack('grid','Page$2')">2</a></td></tr></table>''')
        self.assertEqual([r['id'] for r in listing.reports],[1])
        self.assertIn(2,listing.pages)
        self.assertEqual(listing.hidden['__VIEWSTATE'],'token')


if __name__=='__main__':unittest.main()
