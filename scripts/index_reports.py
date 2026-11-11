"""Incrementally index downloaded workbooks into SQLite for the web app.

python3 scripts/index_reports.py [--watch] [--retry-errors]
Source amounts are validated with Decimal before storage. The web layer uses
numeric approximations for charting; original Excel files remain authoritative.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from analyze_reports import analyze
from download_reports import ROOT, atomic_json, read_json

DB = ROOT / 'data/archive.sqlite3'
PARSER_VERSION = 5


def connect(path=DB):
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    return connection


def init_db():
    DB.parent.mkdir(exist_ok=True)
    with connect() as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('''
        CREATE TABLE IF NOT EXISTS workbooks (
          sha TEXT PRIMARY KEY, file TEXT NOT NULL UNIQUE, source_name TEXT,
          report_id INTEGER, title TEXT, effective_date TEXT, published_at TEXT,
          url TEXT, detail_url TEXT, bytes INTEGER, date TEXT, state TEXT NOT NULL,
          error TEXT, issues TEXT, daily TEXT, parser_version INTEGER, indexed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS flows (
          workbook_sha TEXT NOT NULL REFERENCES workbooks(sha) ON DELETE CASCADE,
          symbol TEXT NOT NULL, company TEXT NOT NULL, search_text TEXT NOT NULL,
          turnover_rial REAL, volume REAL, retail_buy_rial REAL, institutional_buy_rial REAL,
          retail_sell_rial REAL, institutional_sell_rial REAL, retail_net_rial REAL,
          retail_net_volume REAL, retail_buy_value_share REAL, retail_sell_value_share REAL,
          retail_flow_turnover_ratio REAL, retail_buy_vwap_rial REAL, retail_sell_vwap_rial REAL,
          institutional_buy_vwap_rial REAL, institutional_sell_vwap_rial REAL,
          PRIMARY KEY(workbook_sha,symbol)
        );
        CREATE INDEX IF NOT EXISTS flows_symbol ON flows(symbol);
        CREATE INDEX IF NOT EXISTS workbooks_date ON workbooks(date);
        ''')

        if 'source_data' not in {r[1] for r in db.execute('PRAGMA table_info(flows)')}:
            db.execute("ALTER TABLE flows ADD COLUMN source_data TEXT NOT NULL DEFAULT '{}'")
        db.executescript("""
        DROP VIEW IF EXISTS active_reports;
        CREATE VIEW active_reports AS
          SELECT * FROM (
            SELECT *, ROW_NUMBER() OVER (
              PARTITION BY date ORDER BY (state='ready') DESC, COALESCE(published_at,'') DESC, report_id DESC, sha
            ) AS revision_rank FROM workbooks
            WHERE date IS NOT NULL AND (state='ready' OR json_extract(daily,'$.quality.market_eligible')=1)
          ) WHERE revision_rank=1;
        DROP VIEW IF EXISTS symbol_reports;
        CREATE VIEW symbol_reports AS
          SELECT * FROM (
            SELECT *, ROW_NUMBER() OVER (
              PARTITION BY date ORDER BY COALESCE(json_extract(daily,'$.quality.market_eligible'),state='ready') DESC,
              COALESCE(json_extract(daily,'$.quality.value.usable_rows'),0) DESC,
              (state='ready') DESC, COALESCE(published_at,'') DESC, report_id DESC, sha
            ) AS revision_rank FROM workbooks
            WHERE date IS NOT NULL AND (state='ready' OR json_extract(daily,'$.quality.symbol_eligible')=1)
          ) WHERE revision_rank=1;
        """)


def normalize(text):
    return text.replace('ي', 'ی').replace('ك', 'ک').replace('\u200c', '').replace(' ', '').lower()


def ingest(entry, retry=False):
    path = ROOT / entry['file']
    digest = entry.get('sha256') or hashlib.sha256(path.read_bytes()).hexdigest()
    with connect() as db:
        existing = db.execute('SELECT parser_version,state,published_at,report_id FROM workbooks WHERE sha=?', (digest,)).fetchone()
        if existing and existing['parser_version'] == PARSER_VERSION and not (retry and existing['state'] != 'ready'):
            # The same bytes may be republished. Update provenance without re-parsing.
            if (entry.get('published_at') or '') > (existing['published_at'] or ''):
                db.execute('UPDATE workbooks SET published_at=?, report_id=? WHERE sha=?',
                           (entry.get('published_at'), entry['report_id'], digest))
            return False
    timestamp = datetime.now(timezone.utc).isoformat()
    day, records, issues, error = None, [], [], None
    try:
        if path.suffix.lower() == '.xls':
            raise ValueError('Legacy XLS format; original download available, analysis not supported')
        day, records, issues = analyze(path)
        if not records:
            raise ValueError('No instrument rows found in this workbook layout')
        state = 'warning' if issues else 'ready'
    except Exception as exc:
        state, error = 'unsupported', f'{type(exc).__name__}: {exc}'
    meta = dict(sha=digest, file=entry['file'], source_name=entry.get('source_name', path.name),
                report_id=entry['report_id'], title=entry.get('title'), effective_date=entry.get('effective_date'),
                published_at=entry.get('published_at'), url=entry.get('url'), detail_url=entry.get('detail_url'),
                bytes=path.stat().st_size, date=day['date'] if day else None, state=state, error=error,
                issues=json.dumps(issues, ensure_ascii=False),
                daily=json.dumps(day, ensure_ascii=False, default=str) if day else None,
                parser_version=PARSER_VERSION, indexed_at=timestamp)
    columns = list(meta)
    flow_keys = ['turnover_rial','volume','retail_buy_rial','institutional_buy_rial',
                 'retail_sell_rial','institutional_sell_rial','retail_net_rial',
                 'retail_net_volume','retail_buy_value_share','retail_sell_value_share',
                 'retail_flow_turnover_ratio','retail_buy_vwap_rial','retail_sell_vwap_rial',
                 'institutional_buy_vwap_rial','institutional_sell_vwap_rial']
    with connect() as db:
        db.execute('DELETE FROM workbooks WHERE sha=?', (digest,))
        db.execute(f'INSERT INTO workbooks ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})', list(meta.values()))
        insert_columns = ['workbook_sha','symbol','company','search_text',*flow_keys,'source_data']
        db.executemany(f'INSERT INTO flows ({",".join(insert_columns)}) VALUES ({",".join("?" for _ in insert_columns)})',
                       [(digest, r['symbol'], r['company'], normalize(r['symbol']+' '+r['company']),
                         *[float(r[k]) if r[k] not in ('',None) else None for k in flow_keys],
                         json.dumps(r['source_data'],ensure_ascii=False,default=str)) for r in records])
    print(f"{state}: {path.name} ({len(records)} rows){': '+error if error else ''}", flush=True)
    return True


def index_once(retry=False):
    entries = read_json(ROOT / 'data/download-manifest.json', [])
    # Analyze newer reports first; deduplicate shared content before parsing.
    by_hash = {}
    for entry in sorted(entries, key=lambda e: e.get('published_at') or '', reverse=True):
        by_hash.setdefault(entry.get('sha256', entry['file']), entry)
    changed = 0
    status = {'phase': 'indexing', 'total': len(by_hash), 'processed': 0, 'changed': 0}
    for entry in by_hash.values():
        try:
            changed += ingest(entry, retry)
        except Exception as exc:
            print(f"Index error for {entry['file']}: {exc}", flush=True)
        status.update(processed=status['processed']+1, changed=changed, updated_at=datetime.now(timezone.utc).isoformat())
        atomic_json(ROOT / 'data/index-status.json', status)
    status.update(phase='complete')
    atomic_json(ROOT / 'data/index-status.json', status)
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--retry-errors', action='store_true')
    args = parser.parse_args()
    init_db()
    with (ROOT / 'data/index.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(2, 'Another indexer is running.\n')
        last_manifest_mtime = None
        while True:
            manifest = ROOT / 'data/download-manifest.json'
            mtime = manifest.stat().st_mtime_ns if manifest.exists() else 0
            if mtime != last_manifest_mtime:
                index_once(args.retry_errors)
                last_manifest_mtime = mtime
            if not args.watch:
                break
            time.sleep(8)


if __name__ == '__main__':
    main()
