"""Resumable, deduplicated downloader for every page of TSE category 12.

python3 scripts/download_reports.py             # all pages (default)
python3 scripts/download_reports.py --limit 20  # recent sample
Only Python's standard library is required. Metadata is checkpointed after every
attachment. File IDs skip repeat downloads; SHA-256 deduplicates identical bytes.
Different revisions sharing a filename are retained under distinct filenames.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
from pathlib import Path
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://webgw.tse.ir/cmssite/api/v1/'


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def get(url):
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={
                'User-Agent': 'TSE archive research/1.0', 'Referer': 'https://www.tse.ir/'})
            with urllib.request.urlopen(request, timeout=35) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == 3:
                raise
            time.sleep(min(2 ** attempt, 8))


def workbook_bytes(payload, suffix):
    if suffix in ('.xlsx', '.xlsm'):
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            if 'xl/workbook.xml' not in archive.namelist():
                raise ValueError('Attachment is not an Excel workbook')
    elif not payload.startswith(bytes.fromhex('D0CF11E0A1B11AE1')):
        raise ValueError('Attachment is not an XLS workbook')


class Downloader:
    def __init__(self, limit=0, workers=4):
        self.limit, self.workers = limit, workers
        self.folder = ROOT / 'data'
        (self.folder / 'raw').mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.folder / 'download-manifest.json'
        self.entries = read_json(self.manifest_path, [])
        self.lock = threading.Lock()
        self.by_id, self.by_hash = {}, {}
        self.errors = []
        self.status = {'phase': 'catalog', 'started_at': now(), 'updated_at': now(),
                       'pages_scanned': 0, 'pages_total': 0, 'reports_found': 0,
                       'attachments_total': 0, 'processed': 0, 'downloaded': 0,
                       'reused': 0, 'duplicates': 0, 'failed': 0}
        # Migrate the previous manifest without losing its 20 files.
        for entry in self.entries:
            path = ROOT / entry['file']
            if path.is_file():
                entry.setdefault('file_id', entry.get('url', '').rsplit('/', 1)[-1])
                entry.setdefault('source_name', path.name)
                payload = path.read_bytes()
                digest = hashlib.sha256(payload).hexdigest()
                if entry.get('sha256') and entry['sha256'] != digest:
                    # A damaged or manually replaced local file must be fetched
                    # again, not blessed as the same source attachment.
                    continue
                try:
                    workbook_bytes(payload, path.suffix.lower())
                except (ValueError, zipfile.BadZipFile):
                    continue
                entry['sha256'] = digest
                self.by_id[entry['file_id']] = entry
                self.by_hash[digest] = entry['file']

    def checkpoint(self):
        self.status['updated_at'] = now()
        self.status['failed'] = len(self.errors)
        atomic_json(self.manifest_path, sorted(self.entries, key=lambda e: (e['effective_date'], str(e['report_id']), e.get('file_id', ''))))
        atomic_json(self.folder / 'download-errors.json', self.errors)
        atomic_json(self.folder / 'download-status.json', self.status)

    def page(self, number):
        query = urllib.parse.urlencode({'EDeliveryCategoryIds': 12, 'PageNumber': number, 'PageSize': 20})
        return json.loads(get(BASE + 'EDeliveryObject/List/fa?' + query))

    def catalog(self):
        cached = read_json(self.folder / 'report-catalog.json', {})
        found = {str(item['content']['id']): item for item in cached.get('items', [])}
        first = self.page(1)
        pages = first['totalPages']
        self.status.update(pages_total=pages, source_total=first['totalCount'])
        # Always walk the requested pages. Existing entries do not terminate discovery.
        count_pages = min(pages, (self.limit + 19) // 20) if self.limit else pages
        def save(number, result):
            for item in result['items']:
                found[str(item['content']['id'])] = item
            self.status['pages_scanned'] += 1
            self.status['reports_found'] = len(found)
            atomic_json(self.folder / 'report-catalog.json', {'fetched_at': now(), 'total_count': first['totalCount'], 'items': list(found.values())})
            self.checkpoint()
            print(f'Catalog page {number}/{pages}; {len(found)} unique reports', flush=True)
        save(1, first)
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {pool.submit(self.page, number): number for number in range(2, count_pages + 1)}
            for future in as_completed(futures):
                number = futures[future]
                try:
                    save(number, future.result())
                except Exception as error:
                    self.errors.append({'page': number, 'stage': 'catalog', 'error': str(error)})
                    self.checkpoint()
        items = sorted(found.values(), key=lambda item: (item['effectiveFrom'], item['content'].get('publishAt', '')), reverse=True)
        return items[:self.limit] if self.limit else items

    def attachment(self, item, attachment):
        report_id, file_id = item['content']['id'], attachment['fileId']
        suffix = Path(attachment['fileName']).suffix.lower()
        url = attachment.get('link') or f'https://webgw.tse.ir/File/Download/{urllib.parse.quote(file_id)}'
        entry = {'report_id': report_id, 'file_id': file_id, 'title': item['title'],
                 'effective_date': item['effectiveFrom'], 'published_at': item['content'].get('publishAt'),
                 'source_name': attachment['fileName'], 'url': url,
                 'detail_url': f'https://www.tse.ir/delivery-detail?id={report_id}'}
        with self.lock:
            known = self.by_id.get(file_id)
            if known:
                entry.update({key: known[key] for key in ('file', 'sha256', 'bytes')})
                # Same attachment under another report is one physical file, with both source records retained.
                if not any(e['report_id'] == report_id and e.get('file_id') == file_id for e in self.entries):
                    self.entries.append(entry)
                self.status['reused'] += 1
                self.status['processed'] += 1
                self.checkpoint()
                return
        payload = get(url)
        workbook_bytes(payload, suffix)
        digest = hashlib.sha256(payload).hexdigest()
        with self.lock:
            if digest in self.by_hash:
                relative = self.by_hash[digest]
                self.status['duplicates'] += 1
            else:
                safe = re.sub(r'[\\/\x00-\x1f]', '_', attachment['fileName'])
                target = self.folder / 'raw' / safe
                if target.exists():
                    if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                        target = target.with_name(f'{target.stem}--{digest[:12]}{suffix}')
                temporary = target.with_suffix(target.suffix + '.part')
                temporary.write_bytes(payload)
                temporary.replace(target)
                relative = str(target.relative_to(ROOT))
                self.by_hash[digest] = relative
                self.status['downloaded'] += 1
            entry.update(file=relative, sha256=digest, bytes=len(payload), downloaded_at=now())
            self.entries = [e for e in self.entries if not (e['report_id'] == report_id and e.get('file_id') == file_id)]
            self.entries.append(entry)
            self.by_id[file_id] = entry
            self.status['processed'] += 1
            self.checkpoint()
            print(f"{self.status['processed']}/{self.status['attachments_total']}: {attachment['fileName']}", flush=True)

    def run(self):
        try:
            self.checkpoint()
            items = self.catalog()
            tasks = []
            seen_ids = set()
            for item in items:
                for attachment in item['content'].get('files', []):
                    if Path(attachment['fileName']).suffix.lower() in ('.xlsx', '.xlsm', '.xls'):
                        if attachment['fileId'] in seen_ids:
                            continue
                        seen_ids.add(attachment['fileId'])
                        tasks.append((item, attachment))
            self.status.update(phase='downloading', attachments_total=len(tasks))
            self.checkpoint()
            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                futures = {pool.submit(self.attachment, *task): task for task in tasks}
                for future in as_completed(futures):
                    item, attachment = futures[future]
                    try:
                        future.result()
                    except Exception as error:
                        with self.lock:
                            self.errors.append({'report_id': item['content']['id'], 'file_id': attachment['fileId'], 'stage': 'download', 'error': str(error)})
                            self.status['processed'] += 1
                            self.checkpoint()
            self.status.update(phase='complete' if not self.errors else 'partial', completed_at=now())
            self.checkpoint()
        except BaseException as error:
            self.status.update(phase='interrupted' if isinstance(error, KeyboardInterrupt) else 'error', message=str(error))
            self.checkpoint()
            raise
        print(json.dumps(self.status), flush=True)
        return not self.errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=0, help='0 (default) scans every page')
    parser.add_argument('--workers', type=int, default=4, choices=range(1, 9))
    args = parser.parse_args()
    if args.limit < 0:
        parser.error('--limit must be nonnegative')
    (ROOT / 'data').mkdir(exist_ok=True)
    with (ROOT / 'data/download.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(2, 'Another archive download is running.\n')
        success = Downloader(args.limit, args.workers).run()
    if not success:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
