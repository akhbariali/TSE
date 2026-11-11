"""Extract cached Excel values and ownership flows without external dependencies.

Run after download_reports.py. Values retain the source's rial/share units.
No instrument-class assumptions are made; exact symbol suffixes are retained.
"""
import csv
from decimal import Decimal
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
from workbook_layout import (read_workbook as workbook, daily_sheets, normalized,
                             decimal_value, measure, role, action, col_number)


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
    totals = {}
    shares = {}
    for index, row in sorted(summary.items()):
        for col, label in row.items():
            text = normalized(label)
            kind = measure(label)
            if kind and ('معاملات' in text or 'total' in text) and not ('درصد' in text or '%' in text):
                following = summary.get(index + 1, {}).get(col)
                if following is not None:
                    try:
                        number = decimal_value(following, f'summary!{col}{index+1}')
                    except ValueError:
                        continue
                    if kind in totals and totals[kind] != number:
                        raise ValueError(f'Ambiguous summary {kind} totals')
                    totals[kind] = number
            if 'سهام' in text and action(label):
                # Summary percentages describe a narrower instrument scope.
                # Match the value group and explicit retail heading above it.
                header_candidates = [r for n,r in sorted(summary.items()) if index-5 <= n < index
                                     and any(role(t) for t in r.values())
                                     and any(measure(t) for t in r.values())]
                headers = header_candidates[-1] if header_candidates else {}
                groups = [c for c,t in headers.items() if measure(t)]
                for c, heading in headers.items():
                    if role(heading) != 'retail' or col_number(c) <= col_number(col):
                        continue
                    preceding = [g for g in groups if col_number(g)<=col_number(c)]
                    if preceding and measure(headers[max(preceding,key=col_number)]) == 'value':
                        try:
                            shares[action(label)] = decimal_value(row.get(c), f'summary!{c}{index}')
                        except ValueError:
                            pass
    if set(totals) != {'volume','value'}:
        raise ValueError('Summary trading-value/volume total could not be located by labels')
    return totals['volume'], totals['value'], shares.get('buy'), shares.get('sell')


def write_csv(path, records):
    if not records:
        return
    with path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


KEYS = ('retail_buy', 'institutional_buy', 'retail_sell', 'institutional_sell')


def close_amount(actual, expected, kind='value'):
    if actual is None or expected is None:
        return False
    tolerance = max(Decimal(1), abs(expected)*Decimal('1e-14')) if kind=='value' else Decimal(0)
    return abs(actual-expected) <= tolerance


def checked_row(row, kind):
    if not row or row.get('ambiguous') or any(row.get(k) is None for k in KEYS):
        return False
    buy = row['retail_buy'] + row['institutional_buy']
    sell = row['retail_sell'] + row['institutional_sell']
    # Amounts used for flow ratios and VWAPs must agree at the row level.
    return abs(buy-sell) <= (Decimal(1) if kind=='value' else Decimal(0))


def table_quality(table, source_total, issues):
    if table is None:
        return {'rows': 0, 'usable_rows': 0, 'complete': False, 'footer_matches': False}
    usable = [row for row in table.rows.values() if checked_row(row, table.kind)]
    footer_matches = bool(table.totals and len(table.totals)==4)
    for key, expected in (table.totals or {}).items():
        values = [r.get(key) for r in table.rows.values()]
        actual = sum(values) if all(v is not None for v in values) else None
        if not close_amount(actual, expected, table.kind):
            footer_matches = False
            issues.append(f'{table.name}: {key} footer mismatch: {actual} vs {expected}')
    total = sum(r['retail_buy']+r['institutional_buy'] for r in usable)
    summary_matches = close_amount(total, source_total, table.kind)
    if source_total is not None and not summary_matches:
        issues.append(f'{table.kind.capitalize()} summary total mismatch: usable detail {total} vs summary {source_total}')
    # Completeness requires all observed rows to pass and a corroborating total.
    # A missing/corrupt footer must not be bypassed just because a summary matches.
    complete = bool(usable and len(usable)==len(table.rows) and not table.issues
                    and (footer_matches if table.totals is not None else summary_matches))
    return {'rows': len(table.rows), 'usable_rows': len(usable), 'complete': complete,
            'footer_matches': footer_matches, 'summary_matches': summary_matches}


def analyze(path):
    summary, vol_table, val_table = daily_sheets(workbook(path))
    date = report_date(summary, path)
    tables = [t for t in (vol_table, val_table) if t is not None]
    issues = list(dict.fromkeys(issue for t in tables for issue in t.issues))
    try:
        source_volume, source_turnover, buy_share, sell_share = summary_values(summary)
    except ValueError as error:
        source_volume = source_turnover = buy_share = sell_share = None
        issues.append(str(error)+'; using identified detail fields only')
    volume = vol_table.rows if vol_table else {}
    value = val_table.rows if val_table else {}
    for kind,table in [('value',val_table),('volume',vol_table)]:
        if table is None:
            issues.append(f'Missing {kind} ownership table; dependent metrics remain blank')
    if set(volume) != set(value):
        issues.append(f'Volume/value symbol sets differ: {len(set(volume)-set(value))} only in volume, {len(set(value)-set(volume))} only in value')
    records = []
    for symbol in sorted(set(value) | set(volume)):
        row, v = value.get(symbol, {}), volume.get(symbol, {})
        value_valid, volume_valid = checked_row(row, 'value'), checked_row(v, 'volume')
        row_issues = [*row.get('issues', []), *v.get('issues', [])]
        for kind, cells, valid in [('value',row,value_valid), ('volume',v,volume_valid)]:
            if not valid:
                reason = ('buy/sell mismatch' if cells and not cells.get('ambiguous') and all(cells.get(k) is not None for k in KEYS)
                          else 'missing or ambiguous fields')
                message = f'{kind.capitalize()} {reason}: {symbol}; dependent metrics unavailable'
                row_issues.append(message)
                issues.append(message)
        rb, ib, rs, ins = (row.get(k) for k in KEYS)
        rbv, ibv, rsv, inv = (v.get(k) for k in KEYS)
        turnover = rb+ib if value_valid else None
        quantity = rbv+ibv if volume_valid else None
        net = rb-rs if value_valid else None
        records.append({'date':date, 'symbol':symbol, 'company':row.get('company') or v.get('company',''),
            'retail_buy_rial':rb, 'institutional_buy_rial':ib,
            'retail_sell_rial':rs, 'institutional_sell_rial':ins,
            'turnover_rial':turnover, 'volume':quantity,
            'retail_net_rial':net, 'institutional_net_rial':ib-ins if value_valid else None,
            'retail_net_volume':rbv-rsv if volume_valid else None,
            'retail_buy_value_share':rb/turnover if turnover else None,
            'retail_sell_value_share':rs/turnover if turnover else None,
            'retail_flow_turnover_ratio':net/turnover if turnover else None,
            'retail_buy_vwap_rial':rb/rbv if value_valid and volume_valid and rbv else None,
            'retail_sell_vwap_rial':rs/rsv if value_valid and volume_valid and rsv else None,
            'institutional_buy_vwap_rial':ib/ibv if value_valid and volume_valid and ibv else None,
            'institutional_sell_vwap_rial':ins/inv if value_valid and volume_valid and inv else None,
            'source_data': {'value_sheet':val_table.name if val_table else None,
                            'volume_sheet':vol_table.name if vol_table else None,
                            'value_row':row.get('source_row'), 'volume_row':v.get('source_row'),
                            'volume_amounts':{k:v.get(k) for k in KEYS},
                            'value_amounts':{k:row.get(k) for k in KEYS},
                            'value_valid':value_valid,'volume_valid':volume_valid,
                            'issues':list(dict.fromkeys(row_issues))}})
    vq = table_quality(val_table, source_turnover, issues)
    qq = table_quality(vol_table, source_volume, issues)
    if vq['complete'] and any(symbol not in value and any(row.get(k) is not None and row[k]>0 for k in KEYS)
                              for symbol,row in volume.items()):
        vq['complete'] = False
        issues.append('Value table incomplete: traded symbols in volume have no value rows')
    valid = [r for r in records if r['retail_net_rial'] is not None]
    total = sum(r['turnover_rial'] for r in valid)
    net = sum(r['retail_net_rial'] for r in valid)
    positive = sum(r['retail_net_rial']>0 for r in valid)
    negative = sum(r['retail_net_rial']<0 for r in valid)
    ordered = sorted(valid,key=lambda r:r['turnover_rial'],reverse=True)
    issues = list(dict.fromkeys(issues))
    quality = {'value':vq, 'volume':qq, 'market_eligible':vq['complete'],
               'symbol_eligible':bool(valid), 'retained_rows':len(records),
               'unusable_value_rows':len(records)-len(valid),
               'summary_disagrees':not vq.get('summary_matches',False) or not qq.get('summary_matches',False)}
    daily = {'date':date,'file':path.name,'symbols':len(valid),
        'volume':sum(r['volume'] for r in records if r['volume'] is not None) if qq['complete'] else None,
        'turnover_rial':total,'retail_net_rial':net,
        'source_summary_volume':source_volume,'source_summary_turnover_rial':source_turnover,
        'retail_buy_value_share':sum(r['retail_buy_rial'] for r in valid)/total if total else None,
        'retail_sell_value_share':sum(r['retail_sell_rial'] for r in valid)/total if total else None,
        'summary_retail_buy_share':buy_share,'summary_retail_sell_share':sell_share,
        'retail_net_positive_symbols':positive,'retail_net_negative_symbols':negative,
        'retail_net_zero_symbols':len(valid)-positive-negative,
        'top10_turnover_share':sum(r['turnover_rial'] for r in ordered[:10])/total if total else None,
        'normalizations':[note for t in tables for note in t.notes],
        'layouts':[t.describe() for t in tables], 'quality':quality,'validation_issues':len(issues)}
    return daily, records, issues


def main():
    out = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    days, all_records, checks = [], [], []
    paths = sorted((ROOT / 'data/raw').glob('*.xlsx'))
    for path in paths:
        try:
            day, records, issues = analyze(path)
            if day['quality']['market_eligible']:
                days.append(day)
            all_records.extend(r for r in records if r['retail_net_rial'] is not None)
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
