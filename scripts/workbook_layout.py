"""Read Excel table meaning from headers and merged ranges, never fixed positions.

Only explicit labels and redundant percentage headers establish investor identity.
Unresolvable/missing columns raise LayoutError; absent data is never invented as 0.
"""
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import posixpath
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')


class LayoutError(ValueError):
    pass


def normalized(value):
    text = unicodedata.normalize('NFKC', str(value)).translate(DIGITS).lower()
    text = text.translate(str.maketrans({'ي':'ی', 'ى':'ی', 'ك':'ک', 'ة':'ه', 'ۀ':'ه', 'أ':'ا', 'إ':'ا'}))
    return ''.join(c for c in text if c.isalnum() or c == '%')


def col_number(column):
    result = 0
    for char in column:
        result = result * 26 + ord(char) - 64
    return result


def col_name(number):
    result = ''
    while number:
        number, char = divmod(number - 1, 26)
        result = chr(char + 65) + result
    return result


def cell_ref(reference):
    match = re.fullmatch(r'\$?([A-Z]+)\$?(\d+)', reference)
    return col_number(match[1]), int(match[2])


class SheetRows(dict):
    def __init__(self, name, hidden=False):
        super().__init__()
        self.name, self.hidden, self.merges = name, hidden, []


def read_workbook(path):
    result = {}
    with zipfile.ZipFile(path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(t.text or '' for t in item.findall('.//m:t', NS))
                       for item in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        relationships = {r.get('Id'): r.get('Target') for r in
                         ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).find('m:sheets', NS):
            # Hidden duplicate/raw sheets must never silently substitute for a
            # broken public report: their labels and scopes can differ.
            if sheet.get('state', 'visible') != 'visible':
                continue
            name = sheet.get('name')
            rows = SheetRows(name)
            target = relationships[sheet.get(f'{{{REL}}}id')]
            target = posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'xl/' + target)
            with archive.open(target) as stream:
                for event, element in ET.iterparse(stream, events=('end',)):
                    if element.tag == '{'+NS['m']+'}row':
                        values = {}
                        for cell in element:
                            value = cell.find('m:v', NS)
                            if cell.get('t') == 'inlineStr':
                                text = ''.join(t.text or '' for t in cell.findall('.//m:t', NS))
                            elif value is not None:
                                text = strings[int(value.text)] if cell.get('t') == 's' else value.text
                            else:
                                continue
                            values[re.sub(r'\d', '', cell.get('r'))] = text
                        if values:
                            rows[int(element.get('r'))] = values
                        element.clear()
                    elif element.tag == '{'+NS['m']+'}mergeCell':
                        start, end = element.get('ref').split(':')
                        c1, r1 = cell_ref(start); c2, r2 = cell_ref(end)
                        rows.merges.append((c1, r1, c2, r2))
            result[name] = rows
    return result


def role(text):
    text = normalized(text)
    retail = any(word in text for word in ('حقیقی', 'individual', 'retail', 'naturalperson'))
    institution = any(word in text for word in ('حقوقی', 'institutional', 'legalperson'))
    return ('retail' if retail else 'institutional') if retail != institution else None


def action(text):
    text = normalized(text)
    buy = any(word in text for word in ('خرید', 'buy', 'purchase'))
    sell = any(word in text for word in ('فروش', 'فروخته', 'sell', 'sale'))
    return ('buy' if buy else 'sell') if buy != sell else None


def measure(text):
    text = normalized(text)
    volume = any(word in text for word in ('حجم', 'حجمی', 'تعداد', 'volume', 'quantity'))
    value = any(word in text for word in ('ارزش', 'ارزشی', 'value', 'amount', 'ریال', 'rial'))
    return ('volume' if volume else 'value') if volume != value else None


def percentage(text):
    text = normalized(text)
    return any(word in text for word in ('درصد', 'percent', 'share', '%'))


def symbol_label(text):
    return normalized(text) in {'نماد','نامنماد','کدنماد','کدفارسینماد','symbol','ticker','instrumentcode'}


def company_label(text):
    return normalized(text) in {'نامشرکت','نامناشر','نامصندوق','ناماوراق','company','companyname','instrumentname','issuer'}


def total_label(text):
    return normalized(text) in {'جمع','جمعکل','جمعکلمعاملات','مجموع','مجموعکل','total','grandtotal'}


def valid_symbol(text):
    value = normalized(text)
    return bool(value and any(c.isalpha() for c in value) and not total_label(value)
                and not symbol_label(value) and not company_label(value))


def decimal_value(value, context='cell'):
    if value is None or str(value).strip() == '':
        raise LayoutError(f'{context}: missing numeric value (not assumed zero)')
    text = str(value).translate(DIGITS).strip().replace(',', '').replace('٬','').replace('٫','.')
    if text.startswith('(') and text.endswith(')'):
        text = '-'+text[1:-1]
    try:
        number = Decimal(text)
        if not number.is_finite():
            raise InvalidOperation
        return number
    except InvalidOperation:
        raise LayoutError(f'{context}: invalid numeric value {value!r}') from None


def context_cells(rows, header_rows, column):
    """Merged cells are authoritative; forward-fill only labeled header groups."""
    number = col_number(column)
    result = []
    for index in header_rows:
        row = rows[index]
        if column in row:
            result.append(row[column])
            continue
        merged = False
        for c1, r1, c2, r2 in getattr(rows, 'merges', []):
            if r1 <= index <= r2 and c1 <= number <= c2:
                anchor = rows.get(r1, {}).get(col_name(c1))
                if anchor:
                    result.append(anchor)
                merged = True
                break
        if not merged:
            # Exporters occasionally omit merge metadata. A left-hand action
            # group may span blank subcolumns until the next explicit heading.
            left = [(col_number(col), text) for col,text in row.items() if col_number(col)<number]
            if left:
                _, text = max(left)
                if action(text) and role(text) is None:
                    result.append(text)
    return result


@dataclass
class Table:
    name: str
    kind: str
    symbol_column: str
    company_column: str | None
    first_row: int
    columns: dict
    rows: dict = field(default_factory=dict)
    totals: dict | None = None
    issues: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    def describe(self):
        return {'sheet': self.name, 'measure': self.kind,
                'symbol_column': self.symbol_column, 'company_column': self.company_column,
                'data_start_row': self.first_row, 'columns': self.columns}


def detect_table(rows):
    name = getattr(rows, 'name', 'worksheet')
    header = None
    symbol_column = company_column = None
    for index, row in sorted(rows.items()):
        if index > 50:
            break
        symbols = [col for col,text in row.items() if symbol_label(text)]
        if symbols:
            if len(symbols) != 1:
                raise LayoutError(f'{name}: ambiguous symbol headers at row {index}')
            header, symbol_column = index, symbols[0]
            company_column = next((col for col,text in row.items() if company_label(text)), None)
            break
    if header is None:
        raise LayoutError(f'{name}: symbol header not found in the first 50 rows')
    first = None
    for index, row in sorted(rows.items()):
        if index <= header or index > header+20:
            continue
        symbol = row.get(symbol_column, '')
        if valid_symbol(symbol) and not role(symbol) and not action(symbol):
            # A role subheader is not an instrument, even if a shifted symbol
            # column intersects it.
            if any(_is_number(v) for col,v in row.items() if col != symbol_column):
                first = index
                break
    if first is None:
        raise LayoutError(f'{name}: no instrument rows below the symbol header')
    header_rows = [index for index in sorted(rows) if header <= index < first]
    all_columns = set(col for index in header_rows for col in rows[index])
    # Include blank header cells represented by a merge or by real data columns.
    all_columns.update(rows[first])
    mappings = {}; partial = []; group_kinds = set()
    for col in sorted(all_columns, key=col_number):
        if col in (symbol_column, company_column):
            continue
        contexts = context_cells(rows, header_rows, col)
        a = next((action(t) for t in reversed(contexts) if action(t)), None)
        r = next((role(t) for t in reversed(contexts) if role(t)), None)
        kind = next((measure(t) for t in reversed(contexts) if measure(t)), None)
        percent = any(percentage(t) for t in contexts)
        if not a:
            continue
        if kind:
            group_kinds.add(kind)
        partial.append((col,a,r,percent))
    if len(group_kinds) != 1:
        # A short form can omit volume/value in the individual group headings;
        # the sheet name or title then provides an explicit unit label.
        labelled = {measure(name), *[measure(v) for i,row in rows.items() if i<header for v in row.values()]}
        labelled.discard(None)
        if not group_kinds and len(labelled)==1:
            group_kinds=labelled
        else:
            raise LayoutError(f'{name}: missing or conflicting volume/value labels')
    kind = next(iter(group_kinds))
    notes = []
    # Recover an omitted investor subheader only from the same action's explicit,
    # redundant percentage headers, and only with a two-column unambiguous pair.
    for a in ('buy','sell'):
        amounts = sorted([p for p in partial if p[1]==a and not p[3]], key=lambda p:col_number(p[0]))
        percents = sorted([p for p in partial if p[1]==a and p[3]], key=lambda p:col_number(p[0]))
        if len(amounts)==2 and len(percents)==2 and {p[2] for p in percents}=={'retail','institutional'}:
            for amount, percent in zip(amounts,percents):
                col,_,r,_=amount
                if r is None:
                    partial[partial.index(amount)] = (col,a,percent[2],False)
                    notes.append(f'{name}: recovered missing {a} investor heading at {col} from its percentage-header pair')
    for col,a,r,percent in partial:
        if percent or not r:
            continue
        key = r+'_'+a
        if key in mappings:
            raise LayoutError(f'{name}: duplicate/ambiguous {key} headings at {mappings[key]} and {col}')
        mappings[key] = col
    required = {'retail_buy','institutional_buy','retail_sell','institutional_sell'}
    missing = sorted(required-set(mappings))
    if missing:
        raise LayoutError(f'{name}: missing required amount columns: {", ".join(missing)}; cannot safely calculate ownership flows')
    expected = {'retail_buy':'D','institutional_buy':'E','retail_sell':'H','institutional_sell':'I'}
    if mappings != expected or symbol_column!='B' or company_column!='C' or first!=5:
        notes.append(f'{name}: columns and row positions normalized using their headers')
    result = Table(name,kind,symbol_column,company_column,first,mappings,notes=notes)
    for index,row in sorted(rows.items()):
        if index < first:
            continue
        symbol = str(row.get(symbol_column,'')).strip()
        if total_label(symbol) or any(total_label(text) for col,text in row.items()
                                             if col not in mappings.values() and col_number(col)<min(map(col_number,mappings.values()))):
            try:
                result.totals={key:decimal_value(row.get(col),f'{name}!{col}{index}') for key,col in mappings.items()}
            except LayoutError as error:
                result.issues.append(str(error))
            if any(valid_symbol(r.get(symbol_column,'')) for n,r in rows.items() if n>index):
                result.notes.append(f'{name}: ignored template/secondary rows after the first total at row {index}')
            break
        if symbol_label(symbol):
            result.issues.append(f'{name}: repeated header at row {index} before a total; later rows excluded')
            break
        if not valid_symbol(symbol):
            # Footer templates often contain zero-filled helper rows. A missing
            # symbol with nonzero amounts is data loss, not a harmless blank.
            if any(_is_number(row.get(col)) and decimal_value(row[col])!=0 for col in mappings.values()):
                result.issues.append(f'{name}: row {index} has amounts without a valid symbol')
            continue
        if symbol in result.rows:
            result.issues.append(f'{name}: duplicate symbol {symbol!r} at row {index}; not overwritten')
            continue
        try:
            values = {key:decimal_value(row.get(col),f'{name}!{col}{index} ({symbol})') for key,col in mappings.items()}
            if any(v<0 for v in values.values()):
                raise LayoutError(f'{name}: negative trading amount for {symbol!r} at row {index}')
        except LayoutError as error:
            result.issues.append(str(error))
            continue
        result.rows[symbol] = {'company': str(row.get(company_column,'')).strip() if company_column else '',
                               'source_row': index, **values}
    if not company_column:
        result.notes.append(f'{name}: company-name column absent; symbols retained without inventing names')
    return result


def _is_number(value):
    try:
        decimal_value(value)
        return True
    except LayoutError:
        return False


def daily_sheets(sheets):
    tables = {}; summary = []; errors = []; ownership_errors = []
    for name, rows in sheets.items():
        if not rows:
            continue
        n = normalized(name)
        # Use names for candidate discovery, then trust the actual table headers.
        ownership = 'مالکیت' in n or 'ownership' in n
        labelled_header = any(symbol_label(v) for i,row in rows.items() if i<=50 for v in row.values())
        if ownership or labelled_header:
            try:
                table = detect_table(rows)
                if table.kind in tables:
                    raise LayoutError(f'Ambiguous daily report: multiple {table.kind} ownership tables')
                tables[table.kind] = table
            except LayoutError as error:
                errors.append(str(error))
                if ownership:
                    ownership_errors.append(str(error))
        if ('خلاصه' in n and 'بازار' in n) or n in {'summary','marketsummary','marketoverview'}:
            summary.append(rows)
    if len(summary)!=1:
        # Renamed summary sheets can still be identified by their actual total labels.
        summary = [rs for rs in sheets.values() if any(
            'معاملات' in normalized(v) and 'حجم' in normalized(v) and ('کل' in normalized(v) or 'total' in normalized(v))
            for i,row in rs.items() if i<=50 for v in row.values())]
    missing = {'volume','value'}-set(tables)
    if missing or len(summary)!=1:
        detail = '; '.join(errors[:5])
        if not any('مالکیت' in normalized(n) for n in sheets) and not tables:
            detail = 'This workbook is not a supported daily ownership report (for example, a monthly/market-review layout)'
        raise LayoutError(f'Missing or ambiguous daily tables: {", ".join(sorted(missing)) or "summary"}. {detail}')
    # Never silently ignore a broken ownership sheet merely because a second
    # candidate happened to parse. Conflicting interpretations need review.
    if ownership_errors or any('multiple' in e or 'Ambiguous' in e for e in errors):
        raise LayoutError('; '.join(errors))
    return summary[0],tables['volume'],tables['value']
