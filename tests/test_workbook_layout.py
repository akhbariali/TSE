"""Synthetic workbooks exercise layout changes without committing source Excel files."""
from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import unittest
from xml.sax.saxutils import escape
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from workbook_layout import (SheetRows, detect_table, LayoutError, decimal_value,
                             read_workbook, daily_sheets)
from analyze_reports import analyze, summary_values
from unittest.mock import patch


def ownership(kind='value', shifted=0, reverse=False):
    rows=SheetRows('Renamed '+kind)
    rows[2+shifted]={'B':'نماد','C':'نام شرکت','D':f'خرید {"ارزش" if kind=="value" else "حجم"}',
                     'F':'درصد خرید','H':f'فروش {"ارزش" if kind=="value" else "حجم"}','J':'درصد فروش'}
    roles=['حقوقي','حقيقي'] if reverse else ['حقیقی','حقوقی']
    rows[3+shifted]=dict(zip(['D','E','F','G','H','I','J','K'],roles*4))
    rows[4+shifted]={'A':'1','B':'نماد1','C':'شرکت','D':'60','E':'40','H':'30','I':'70'}
    rows[5+shifted]={'A':'2','B':'جمع کل','C':'0','D':'60','E':'40','H':'30','I':'70'}
    return rows


def write_xlsx(path, sheets):
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    rel='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="{rel}"><sheets>'+''.join(
            f'<sheet name="{escape(name)}" sheetId="{i}" r:id="r{i}"/>' for i,name in enumerate(sheets,1))+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships>'+''.join(
            f'<Relationship Id="r{i}" Target="worksheets/s{i}.xml"/>' for i in range(1,len(sheets)+1))+'</Relationships>')
        for i,rows in enumerate(sheets.values(),1):
            xml=f'<worksheet xmlns="{ns}"><sheetData>'
            for n,row in rows.items():
                xml+=f'<row r="{n}">'+''.join(f'<c r="{col}{n}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>' for col,value in row.items())+'</row>'
            xml+='</sheetData><mergeCells>'+''.join(f'<mergeCell ref="{ref}"/>' for ref in ['D2:E2','F2:G2','H2:I2','J2:K2'])+'</mergeCells></worksheet>'
            z.writestr(f'xl/worksheets/s{i}.xml',xml)


class LayoutTests(unittest.TestCase):
    def test_reversed_investors_and_shifted_rows(self):
        t=detect_table(ownership(shifted=7,reverse=True))
        self.assertEqual(t.first_row,11)
        self.assertEqual(t.rows['نماد1']['retail_buy'],40)
        self.assertEqual(t.rows['نماد1']['retail_sell'],70)

    def test_moved_columns_with_combined_english_headings(self):
        r=SheetRows('other')
        r[8]={'F':'ticker','A':'company','L':'buy value institutional','D':'sell value retail',
              'H':'buy value retail','B':'sell value institutional'}
        r[9]={'F':'ABC1','A':'Alpha','L':'40','D':'30','H':'60','B':'70'}
        t=detect_table(r)
        self.assertEqual(t.rows['ABC1']['retail_buy'],60)
        self.assertEqual(t.symbol_column,'F')

    def test_missing_company_column_is_optional(self):
        r=ownership()
        for row in r.values():row.pop('C',None)
        t=detect_table(r)
        self.assertEqual(t.rows['نماد1']['company'],'')
        self.assertTrue(any('company-name' in n for n in t.notes))

    def test_missing_heading_recovered_only_with_redundant_evidence(self):
        r=ownership();del r[3]['D']
        t=detect_table(r)
        self.assertEqual(t.columns['retail_buy'],'D')
        self.assertTrue(any('recovered' in n for n in t.notes))
        del r[3]['F']
        t=detect_table(r)
        self.assertIsNone(t.rows['نماد1']['retail_buy'])
        self.assertTrue(t.issues)

    def test_conflicting_investor_headings_quarantine_only_ambiguous_field(self):
        r=ownership();r[3]['E']='حقیقی'
        t=detect_table(r)
        self.assertIsNone(t.rows['نماد1']['retail_buy'])
        self.assertEqual(t.rows['نماد1']['retail_sell'],30)
        self.assertTrue(any('duplicate/ambiguous' in issue for issue in t.issues))

    def test_missing_and_invalid_amounts_are_not_zero(self):
        for value in [None,'bad','#REF!','NaN']:
            r=ownership()
            if value is None:del r[4]['D']
            else:r[4]['D']=value
            t=detect_table(r)
            self.assertIsNone(t.rows['نماد1']['retail_buy'])
            self.assertEqual(t.rows['نماد1']['retail_sell'],30)
            self.assertTrue(t.issues)

    def test_total_in_index_column_and_secondary_table(self):
        r=ownership();r[5]['A']='جمع كل';del r[5]['B']
        r[7]={**r[4],'D':'999999'}
        t=detect_table(r)
        self.assertEqual(len(t.rows),1)
        self.assertEqual(t.rows['نماد1']['retail_buy'],60)
        self.assertIsNotNone(t.totals)
        self.assertTrue(any('secondary' in n for n in t.notes))

    def test_duplicate_symbol_never_overwrites(self):
        r=ownership();r[6]=r.pop(5);r[5]={**r[4],'D':'999'}
        t=detect_table(r)
        self.assertEqual(t.rows['نماد1']['retail_buy'],60)
        self.assertTrue(any('duplicate symbol' in n for n in t.issues))
        self.assertTrue(t.rows['نماد1']['ambiguous'])

    def test_strict_numeric_normalization_and_precision(self):
        self.assertEqual(decimal_value('۱۲۳٬۴۵۶٫۷'),Decimal('123456.7'))
        self.assertEqual(decimal_value('(1,234)'),-1234)
        self.assertEqual(decimal_value('596948215456567'),Decimal('596948215456567'))
        for v in ['',None,'Infinity']:
            with self.assertRaises(LayoutError):decimal_value(v)

    def test_summary_columns_can_move(self):
        self.assertEqual(summary_values({4:{'B':'حجم کل معاملات','L':'ارزش کل معاملات'},
                                         5:{'B':'100','L':'100'}})[:2],(100,100))

    def test_end_to_end_renamed_sheets_and_merged_headers(self):
        summary={1:{'A':'1405/08/19'},4:{'B':'حجم کل معاملات','L':'ارزش کل معاملات'},5:{'B':'100','L':'100'}}
        sheets={'Market summary':summary,'Sheet volume':ownership('volume',reverse=True),
                'Sheet value':ownership('value',reverse=True)}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fixture.xlsx';write_xlsx(p,sheets)
            day,records,issues=analyze(p)
            self.assertEqual(issues,[])
            self.assertEqual(day['retail_net_rial'],-30)
            self.assertEqual(len(records),1)
            self.assertEqual(len(day['layouts']),2)
            self.assertEqual(day['volume'],100)

    def test_missing_metric_column_keeps_other_fields_without_guessing(self):
        r=ownership()
        for row in r.values():
            row.pop('D',None);row.pop('F',None)
        t=detect_table(r)
        self.assertIsNone(t.rows['نماد1']['retail_buy'])
        self.assertTrue(t.issues)

    def test_buy_and_sell_summary_shares_follow_retail_headers(self):
        r={4:{'B':'حجم کل معاملات','L':'ارزش کل معاملات'},5:{'B':'100','L':'100'},
           8:{'F':'تفکیک ارزش معاملات درصد','H':'حقوقی','I':'حقیقی'},
           9:{'F':'سهام خریداری شده','H':'0.4','I':'0.6'},
           10:{'F':'سهام فروخته شده','H':'0.7','I':'0.3'}}
        self.assertEqual(summary_values(r)[2:],(Decimal('0.6'),Decimal('0.3')))

    def test_broken_named_ownership_sheet_is_not_silently_ignored(self):
        summary={4:{'B':'حجم کل معاملات','L':'ارزش کل معاملات'},5:{'B':'100','L':'100'}}
        sheets={'Market summary':summary,'v':ownership('volume'),'a':ownership(),
                'تغییر مالکیت خراب':{1:{'A':'unrecognizable'}}}
        _,volume,value=daily_sheets(sheets)
        self.assertTrue(any('symbol header' in note for note in value.notes))
        self.assertEqual(len(volume.rows),1)

    def test_conflicting_daily_tables_rejected(self):
        summary={4:{'B':'حجم کل معاملات','L':'ارزش کل معاملات'},5:{'B':'100','L':'100'}}
        sheets={'Market summary':summary,'v':ownership('volume'),'a':ownership(),'b':ownership()}
        with self.assertRaisesRegex(LayoutError,'multiple'):daily_sheets(sheets)


class PartialDataTests(unittest.TestCase):
    def parse(self, value=None, volume=None, summary_total='100'):
        sheets={'Market summary':{1:{'A':'1405/08/19'},
                4:{'B':'حجم کل معاملات','L':'ارزش کل معاملات'},
                5:{'B':summary_total,'L':summary_total}}}
        if value is not None:sheets['value']=value
        if volume is not None:sheets['volume']=volume
        with patch('analyze_reports.workbook',return_value=sheets):
            return analyze(Path('fixture.xlsx'))

    def test_summary_disagreement_keeps_reconciled_detail(self):
        day,records,issues=self.parse(ownership(),ownership('volume'),summary_total='200')
        self.assertTrue(issues)
        self.assertTrue(day['quality']['market_eligible'])
        self.assertEqual(day['turnover_rial'],100)
        self.assertEqual(day['source_summary_turnover_rial'],200)
        self.assertEqual(records[0]['retail_net_rial'],30)

    def test_value_only_report_supports_value_metrics_without_volume_or_vwap(self):
        day,records,issues=self.parse(value=ownership())
        self.assertTrue(day['quality']['market_eligible'])
        self.assertTrue(day['quality']['symbol_eligible'])
        self.assertIsNone(day['volume'])
        self.assertEqual(records[0]['retail_net_rial'],30)
        self.assertIsNone(records[0]['retail_buy_vwap_rial'])
        self.assertIsNone(records[0]['volume'])

    def test_missing_cell_preserves_other_fields_but_blocks_dependent_metrics(self):
        value=ownership();del value[4]['D']
        day,records,issues=self.parse(value,ownership('volume'))
        record=records[0]
        self.assertIsNone(record['retail_buy_rial'])
        self.assertEqual(record['retail_sell_rial'],30)
        self.assertEqual(record['volume'],100)
        self.assertIsNone(record['retail_net_rial'])
        self.assertIsNone(record['retail_buy_vwap_rial'])
        self.assertFalse(day['quality']['market_eligible'])

    def test_contradictory_row_does_not_enter_aggregate(self):
        value=ownership();value[4]['D']='61'
        # A discrepancy greater than the one-rial cached-value allowance.
        value[4]['D']='65'
        value[6]=value.pop(5)
        value[5]={'A':'2','B':'نماد2','C':'شرکت2','D':'60','E':'40','H':'30','I':'70'}
        day,records,issues=self.parse(value,ownership('volume'))
        self.assertEqual(day['symbols'],1)
        self.assertEqual(day['turnover_rial'],100)
        self.assertFalse(day['quality']['market_eligible'])
        self.assertTrue(day['quality']['symbol_eligible'])
        self.assertIsNone(records[0]['retail_net_rial'])
        self.assertEqual(records[1]['retail_net_rial'],30)

    def test_volume_failure_does_not_block_value_flow(self):
        volume=ownership('volume');volume[4]['D']='bad'
        day,records,issues=self.parse(ownership(),volume)
        self.assertTrue(day['quality']['market_eligible'])
        self.assertEqual(records[0]['retail_net_rial'],30)
        self.assertIsNone(records[0]['volume'])
        self.assertIsNone(records[0]['retail_buy_vwap_rial'])

    def test_duplicate_symbol_has_no_derived_metrics(self):
        value=ownership();value[6]=value.pop(5);value[5]=dict(value[4])
        day,records,issues=self.parse(value,ownership('volume'))
        self.assertFalse(day['quality']['symbol_eligible'])
        self.assertIsNone(records[0]['retail_net_rial'])

    def test_bad_footer_prevents_market_total_even_with_good_rows(self):
        value=ownership();value[5]['D']='500'
        day,records,issues=self.parse(value,ownership('volume'))
        self.assertFalse(day['quality']['market_eligible'])
        self.assertTrue(day['quality']['symbol_eligible'])
        self.assertEqual(records[0]['retail_net_rial'],30)

    def test_extra_traded_volume_symbol_prevents_claiming_complete_value_table(self):
        volume=ownership('volume');volume[6]=volume.pop(5)
        volume[5]={'A':'2','B':'نماد2','C':'شرکت2','D':'60','E':'40','H':'30','I':'70'}
        day,records,issues=self.parse(ownership(),volume)
        self.assertFalse(day['quality']['market_eligible'])
        self.assertTrue(day['quality']['symbol_eligible'])
        self.assertTrue(any('Value table incomplete' in issue for issue in issues))

    def test_volume_only_report_retains_real_data(self):
        day,records,issues=self.parse(volume=ownership('volume'))
        self.assertEqual(records[0]['volume'],100)
        self.assertEqual(records[0]['retail_net_volume'],30)
        self.assertIsNone(records[0]['retail_net_rial'])
        self.assertFalse(day['quality']['market_eligible'])


if __name__=='__main__':unittest.main()
