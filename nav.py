"""Private shared-portfolio unit accounting. All monetary inputs are tomans."""
from decimal import Decimal, InvalidOperation
from contextlib import contextmanager
import json
import re
from pathlib import Path
import sqlite3

DB = Path(__file__).resolve().parent / 'data/nav.sqlite3'
EXCLUDED = {'وتوصا', 'خاور', 'خصدرا', 'توان', 'آب', 'کاوان', 'vetoosa', 'khavar', 'khesadra', 'tavan', 'ab', 'kavan'}


def symbol_key(value):
    return ''.join(value.replace('ي', 'ی').replace('ك', 'ک').lower().split()).replace('\u200c', '').rstrip('1۱')


def default_book():
    return {'owner': 'Me', 'people': ['Me', 'Person 2'], 'flows': [
        {'person': 'Me', 'date': '', 'amount': '5000000', 'unit_price': '1'},
        {'person': 'Person 2', 'date': '', 'amount': '5000000', 'unit_price': '1'}],
        'holdings': [], 'cash': '', 'liabilities': '0', 'as_of': '', 'confirmed': False,
        'note': 'Opening contributions supplied by owner. Opening date not yet specified.'}


def number(value, label, signed=False):
    try:
        if isinstance(value, bool):
            raise ValueError()
        result = Decimal(str(value))
        if not result.is_finite() or abs(result) > Decimal('1e18') or (not signed and result < 0):
            raise ValueError()
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'{label}: enter a valid {"" if signed else "nonnegative "}number.') from None


def calculate(book):
    if not isinstance(book, dict):
        raise ValueError('Invalid portfolio.')
    people, flows, holdings = book.get('people'), book.get('flows'), book.get('holdings')
    if not isinstance(people, list) or not 1 <= len(people) <= 100 or any(not isinstance(p, str) or not p.strip() or len(p) > 100 for p in people) or len(set(people)) != len(people):
        raise ValueError('Provide unique participant names.')
    if book.get('owner', 'Me') not in people:
        raise ValueError('Select your participant so your balance stays private.')
    if not isinstance(flows, list) or len(flows) > 5000 or not isinstance(holdings, list) or len(holdings) > 500:
        raise ValueError('Invalid ledger size.')
    balances = {p: {'units': Decimal(0), 'net_contributed': Decimal(0)} for p in people}
    last_date = ''
    for f in flows:
        if not isinstance(f, dict) or f.get('person') not in balances:
            raise ValueError('Every cash flow needs an existing participant.')
        date = f.get('date', '')
        if not isinstance(date, str) or (date and not re.fullmatch(r'\d{4}/(0[1-9]|1[0-2])/(0[1-9]|[12]\d|30|31)', date)) or (last_date and (not date or date < last_date)):
            raise ValueError('Keep cash flows in date order; opening undated entries must come first.')
        last_date = date
        amount = number(f.get('amount'), 'Cash flow', signed=True)
        unit_price = number(f.get('unit_price'), 'Entry NAV')
        if unit_price <= 0 or amount == 0:
            raise ValueError('Cash flows must be nonzero and entry NAV must be positive.')
        person = balances[f['person']]
        person['units'] += amount / unit_price
        person['net_contributed'] += amount
        if person['units'] < Decimal('-0.00000001'):
            raise ValueError('A withdrawal cannot redeem more units than the person owns.')
    total_units = sum(p['units'] for p in balances.values())
    included = Decimal(0)
    excluded = Decimal(0)
    details = []
    for h in holdings:
        if not isinstance(h, dict) or not isinstance(h.get('symbol'), str) or not h['symbol'].strip() or len(h['symbol']) > 100:
            raise ValueError('Each holding needs a symbol.')
        value = number(h.get('value'), 'Holding value')
        personal = symbol_key(h['symbol']) in EXCLUDED or h.get('personal') is True
        if personal:
            excluded += value
        else:
            included += value
        details.append({'symbol': h['symbol'], 'value': float(value), 'personal': personal})
    confirmed = book.get('confirmed') is True
    if type(book.get('estimated', False)) is not bool:
        raise ValueError('Estimated valuation must be true or false.')
    as_of = book.get('as_of', '')
    if not isinstance(as_of, str) or len(as_of) > 100 or not isinstance(book.get('note', ''), str) or len(book.get('note', '')) > 4000:
        raise ValueError('Invalid valuation date or note.')
    cash = number(book['cash'], 'Shared cash', signed=True) if book.get('cash') not in ('', None) else None
    liabilities = number(book.get('liabilities', '0'), 'Liabilities')
    ready = confirmed and cash is not None and bool(as_of.strip())
    if confirmed and not ready:
        raise ValueError('Enter a valuation date and shared cash balance before confirming.')
    nav = included + cash - liabilities if ready else None
    if nav is not None and nav < 0:
        raise ValueError('Shared net assets cannot be negative.')
    if nav is not None and total_units <= 0:
        raise ValueError('A confirmed valuation requires outstanding units.')
    unit_price = nav / total_units if nav is not None else None
    results = []
    for name, person in balances.items():
        value = person['units'] * unit_price if unit_price is not None else None
        profit = value - person['net_contributed'] if value is not None else None
        results.append({'person': name, 'units': float(person['units']),
                        'net_contributed': float(person['net_contributed']),
                        'ownership': float(person['units'] / total_units) if total_units else 0,
                        'value': float(value) if value is not None else None,
                        'profit': float(profit) if profit is not None else None})
    return {'people': results, 'holdings': details, 'included': float(included), 'excluded': float(excluded),
            'nav': float(nav) if nav is not None else None,
            'unit_price': float(unit_price) if unit_price is not None else None, 'ready': ready}


@contextmanager
def storage():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    try:
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS books (revision INTEGER PRIMARY KEY, document TEXT NOT NULL)')
            yield db
    finally:
        db.close()


def load():
    with storage() as db:
        row = db.execute('SELECT revision,document FROM books ORDER BY revision DESC LIMIT 1').fetchone()
    book = json.loads(row[1]) if row else default_book()
    return {'revision': row[0] if row else 0, 'book': book, 'result': calculate(book)}


def balances():
    """Balance-page response deliberately omits owner and portfolio information."""
    data = load()
    owner = data['book'].get('owner', 'Me')
    return {'as_of': data['book'].get('as_of', ''), 'ready': data['result']['ready'],
            'estimated': data['book'].get('estimated', False),
            'people': [{key: person[key] for key in ('person', 'net_contributed', 'value', 'profit')}
                       for person in data['result']['people'] if person['person'] != owner]}


def save(payload):
    if not isinstance(payload, dict) or type(payload.get('revision')) is not int:
        raise ValueError('A saved revision is required.')
    book = payload.get('book')
    result = calculate(book)
    with storage() as db:
        db.execute('BEGIN IMMEDIATE')
        revision = db.execute('SELECT COALESCE(MAX(revision),0) FROM books').fetchone()[0]
        if payload['revision'] != revision:
            raise ValueError('Portfolio changed in another tab. Reload before saving; your edits have not been saved.')
        db.execute('INSERT INTO books VALUES (?,?)', (revision + 1, json.dumps(book, ensure_ascii=False, allow_nan=False)))
    return {'revision': revision + 1, 'book': book, 'result': result}
