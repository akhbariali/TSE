"""Extract cached Excel values and ownership flows without external dependencies.

Run after download_reports.py. Values retain the source's rial/share units.
No instrument-class assumptions are made; exact symbol suffixes are retained.
"""
import csv
from decimal import Decimal
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def workbook(path):
    with zipfile.ZipFile(path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(t.text or '' for t in x.findall('.//m:t', NS))
                       for x in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        relationships = {r.get('Id'): r.get('Target') for r in
                         ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        result = {}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).find('m:sheets', NS):
            # Hidden sheets repeat the visible report and can contain very large
            # formatting ranges. Read only the three source tables we use.
            if sheet.get('name') not in ('خلاصه بازار', 'تغییر مالکیت براساس حجم', 'تغییر مالکیت براساس ارزش'):
                continue
            target = relationships[sheet.get(f'{{{REL}}}id')]
            target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
            rows = {}
            stream = archive.open(target)
            for event, row in ET.iterparse(stream, events=('end',)):
                if row.tag != '{' + NS['m'] + '}row':
                    continue
                values = {}
                for cell in row:
                    value = cell.find('m:v', NS)
                    if cell.get('t') == 'inlineStr':
                        value_text = ''.join(t.text or '' for t in cell.findall('.//m:t', NS))
                    elif value is not None:
                        value_text = strings[int(value.text)] if cell.get('t') == 's' else value.text
                    else:
                        continue
                    values[re.sub(r'\d', '', cell.get('r'))] = value_text
                if values:
                    rows[int(row.get('r'))] = values
                row.clear()
            stream.close()
            result[sheet.get('name')] = rows
        return result


def numeric(row, col):
    return Decimal(row.get(col, '0'))


def table(rows):
    return {row['B']: row for row in rows.values()
            if row.get('A', '').isdigit() and row.get('B') and row.get('C')}


def report_date(summary, path):
    """Normalize source dates; older layouts put 'مورخ' in D7 and a date in F7."""
    translation = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
    candidates = [str(value).translate(translation) for index, row in sorted(summary.items())
                  if index <= 15 for value in row.values()]
    candidates.append(path.name.translate(translation))
    for candidate in candidates:
        match = re.search(r'(?<!\d)((?:13|14)\d{2})[-/]?(\d{2})[-/]?(\d{2})(?!\d)', candidate)
        if match:
            year, month, day = map(int, match.groups())
            if 1 <= month <= 12 and 1 <= day <= (31 if month <= 6 else 30):
                return f'{year:04}/{month:02}/{day:02}'
    raise ValueError('No valid Solar Hijri report date in the summary or filename')


def summary_values(summary):
    # A few versions add four rows above the same summary. Locate the labels,
    # rather than silently reading a heading or a numeric chart helper cell.
    total = None
    buy_share = sell_share = None
    for index, row in summary.items():
        if 'حجم' in row.get('D', '') and 'معاملات' in row.get('D', '') and 'ارزش' in row.get('F', ''):
            total = summary.get(index + 1)
        label = row.get('F', '')
        if 'سهام' in label:
            try:
                share = numeric(row, 'I')
                if 'خریداری' in label or 'خريداري' in label:
                    buy_share = share
                if 'فروخته' in label:
                    sell_share = share
            except Exception:
                pass
    if total is None:
        raise ValueError('Summary trading-value/volume total could not be located')
    return numeric(total, 'D'), numeric(total, 'F'), buy_share, sell_share


def write_csv(path, records):
    if not records:
        return
    with path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def analyze(path):
    sheets = workbook(path)
    summary = sheets['خلاصه بازار']
    date = report_date(summary, path)
    source_volume, source_turnover, buy_share, sell_share = summary_values(summary)
    vol_rows = sheets['تغییر مالکیت براساس حجم']
    val_rows = sheets['تغییر مالکیت براساس ارزش']
    volume, value = table(vol_rows), table(val_rows)
    records = []
    issues = []
    if set(volume) != set(value):
        issues.append('Volume/value symbol sets differ')
    for symbol, row in value.items():
        v = volume.get(symbol)
        if v is None:
            continue
        rb, ib, rs, ins = (numeric(row, c) for c in ['D', 'E', 'H', 'I'])
        rbv, ibv, rsv, inv = (numeric(v, c) for c in ['D', 'E', 'H', 'I'])
        turnover, quantity = rb + ib, rbv + ibv
        if abs(turnover - rs - ins) > 1 or quantity != rsv + inv:
            issues.append(f'Buy/sell mismatch: {symbol}')
        records.append({'date': date, 'symbol': symbol, 'company': row['C'],
                        'retail_buy_rial': rb, 'institutional_buy_rial': ib,
                        'retail_sell_rial': rs, 'institutional_sell_rial': ins,
                        'turnover_rial': turnover, 'volume': quantity,
                        'retail_net_rial': rb-rs, 'institutional_net_rial': ib-ins,
                        'retail_net_volume': rbv-rsv,
                        'retail_buy_value_share': rb/turnover if turnover else 0,
                        'retail_sell_value_share': rs/turnover if turnover else 0,
                        'retail_flow_turnover_ratio': (rb-rs)/turnover if turnover else 0,
                        'retail_buy_vwap_rial': rb/rbv if rbv else '',
                        'retail_sell_vwap_rial': rs/rsv if rsv else '',
                        'institutional_buy_vwap_rial': ib/ibv if ibv else '',
                        'institutional_sell_vwap_rial': ins/inv if inv else ''})
    total = sum(r['turnover_rial'] for r in records)
    net = sum(r['retail_net_rial'] for r in records)
    # Excel cached totals have ~15 significant digits. Allow only the tiny
    # rounding error at that precision, not a material reconciliation gap.
    tolerance = max(Decimal(1), abs(source_turnover)*Decimal('1e-14'))
    if abs(total-source_turnover) > tolerance:
        issues.append(f'Turnover total mismatch: {total} vs {source_turnover}')
    if sum(r['volume'] for r in records) != source_volume:
        issues.append('Volume total mismatch')
    positive = sum(r['retail_net_rial'] > 0 for r in records)
    negative = sum(r['retail_net_rial'] < 0 for r in records)
    ordered = sorted(records, key=lambda r: r['turnover_rial'], reverse=True)
    daily = {'date': date, 'file': path.name, 'symbols': len(records),
             'volume': source_volume, 'turnover_rial': total, 'retail_net_rial': net,
             'retail_buy_value_share': sum(r['retail_buy_rial'] for r in records)/total if total else None,
             'retail_sell_value_share': sum(r['retail_sell_rial'] for r in records)/total if total else None,
             'summary_retail_buy_share': buy_share,
             'summary_retail_sell_share': sell_share,
             'retail_net_positive_symbols': positive, 'retail_net_negative_symbols': negative,
             'retail_net_zero_symbols': len(records)-positive-negative,
             'top10_turnover_share': sum(r['turnover_rial'] for r in ordered[:10])/total if total else None,
             'validation_issues': len(issues)}
    return daily, records, issues


def main():
    out = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    days, all_records, checks = [], [], []
    paths = sorted((ROOT / 'data/raw').glob('*.xlsx'))
    for path in paths:
        try:
            day, records, issues = analyze(path)
            days.append(day)
            all_records.extend(records)
            checks.append({'file': path.name, 'issues': issues})
        except Exception as error:
            checks.append({'file': path.name, 'error': str(error)})
    days.sort(key=lambda day: day['date'])
    write_csv(out / 'daily-summary.csv', days)
    write_csv(out / 'symbol-flows.csv', all_records)
    (out / 'validation.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2))
    if not days:
        raise RuntimeError('No workbooks could be analyzed')
    latest = [r for r in all_records if r['date'] == days[-1]['date']]
    aggregate = {}
    for r in all_records:
        a = aggregate.setdefault(r['symbol'], {'symbol': r['symbol'], 'company': r['company'],
                'days': 0, 'turnover_rial': Decimal(0), 'retail_net_rial': Decimal(0),
                'positive_days': 0, 'negative_days': 0})
        a['days'] += 1
        a['turnover_rial'] += r['turnover_rial']
        a['retail_net_rial'] += r['retail_net_rial']
        a['positive_days'] += r['retail_net_rial'] > 0
        a['negative_days'] += r['retail_net_rial'] < 0
    agg = sorted(aggregate.values(), key=lambda r: r['retail_net_rial'], reverse=True)
    write_csv(out / 'cumulative-symbol-flows.csv', agg)
    highlights = {'days': days, 'latest_top_retail_net_buys': sorted(latest, key=lambda r:r['retail_net_rial'],reverse=True)[:10],
                  'latest_top_institutional_net_buys': sorted(latest, key=lambda r:r['retail_net_rial'])[:10],
                  'cumulative_top_retail_net_buys': agg[:10], 'cumulative_top_institutional_net_buys': agg[-10:][::-1],
                  'validation': checks}
    (out / 'highlights.json').write_text(json.dumps(highlights, ensure_ascii=False, indent=2, default=str))
    print(json.dumps({'days': len(days), 'first': days[0], 'last': days[-1],
                      'total_retail_net_rial': sum(d['retail_net_rial'] for d in days),
                      'positive_days': sum(d['retail_net_rial']>0 for d in days),
                      'latest_top_retail': highlights['latest_top_retail_net_buys'][:5],
                      'latest_top_institutional': highlights['latest_top_institutional_net_buys'][:5],
                      'validation': checks}, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
