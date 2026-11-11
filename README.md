# TSE Market Archive

A local web app for browsing Tehran Securities Exchange market-performance workbooks and exploring individual/institutional ownership flows. **No login, API key, or external service is required.** The application uses Python 3.10+ and its standard library, with SQLite for incremental storage. The downloader's process locks use `fcntl` (Linux/macOS).

## Run the app

```bash
cd /path/to/TSE
python3 app.py --port 8000
```

Open **http://127.0.0.1:8000**. The existing downloaded files and database are ready to use. The server starts a lightweight background indexer that notices new downloads; it does not automatically start a network download. The UI has no external font, chart-library, or CDN dependency.

To listen on another interface, use `--host 0.0.0.0`. Access remains unauthenticated, including the archive-refresh action. Run it on the intended network. Deployment behind a reverse proxy is possible; this repository does not provision hosting.

## Download the entire archive

```bash
python3 scripts/download_reports.py
python3 scripts/index_reports.py
```

Alternatively, click **Update archive** in the web app. It starts the same downloader in the background; you can keep using the app. Download progress, validation counts, and failures appear in the interface. The process continues if the browser is closed.

- The default is **all pages**, not a 20-report sample.
- `--limit 20` deliberately restricts discovery to a recent sample; it never deletes older successful downloads or truncates the manifest.
- `--workers 4` controls concurrency (1–8).
- Every source page is scanned; an existing report does not terminate pagination.
- Report IDs deduplicate catalog entries, attachment IDs prevent repeat file downloads, and SHA-256 hashes share identical bytes across different attachments.
- Different content with the same source filename is preserved using a hash suffix.
- File writes are atomic. Metadata and errors are checkpointed after every attachment. Successful files survive interrupted and partial runs.
- Re-running retries failed pages/files and reuses successful attachments. A single OS lock prevents concurrent download writers. Known damaged files are fetched again.
- Reports without an Excel attachment remain in `data/report-catalog.json`; the downloader does not invent an Excel version of a PDF-only report.

The current source category exposed **802 report entries across 41 pages**, with **797 Excel attachments and 794 distinct workbook contents**, as retrieved on 11 November 2026. No attachment downloads failed. This is coverage of the currently exposed category, not a claim that TSE retains every historical trading date.

## What the app offers

- Market overview with daily net-transfer bars, cumulative transfers, and trading-value charts.
- Latest 5/20/60 reports, full validated history, or custom Solar Hijri date ranges.
- Pointer or keyboard report inspection, ownership-flow breadth, and original workbook download.
- Symbol/company search, direction and minimum-turnover filters, sortable rankings, and pagination.
- Net transfers, transfer-to-turnover ratios, observed-day buying persistence, and symbol history with investor-category purchase VWAPs.
- Searchable report library with original Excel downloads, publication dates, TSE source links, file sizes, and validation/revision status.
- CSV exports that respect the selected dates and symbol-table filters. Amount fields ending in `_rial` use rials, not the trillion-toman display unit.
- Archive progress and data methodology, with explicit analysis exclusions.

The interface currently uses English, with Persian source labels/symbols retained and Solar Hijri report dates. Gregorian publication dates are explicitly labeled. The original source files are authoritative.

## Data quality and interpretation

After historical-layout/date normalization, **345 workbooks pass the accounting checks; 443 have warnings; 6 are not fully supported**. Warning/unsupported files stay downloadable and searchable, but do not enter chart aggregates. Historical examples include mismatched value/volume symbol sets, source totals that do not reconcile with detailed rows, and monthly report layouts outside the daily parser. Review the exact issue in the library before relying on a file.

Dates are normalized from compact, slash-separated, dash-separated, and Persian-digit formats. Shifted daily summary rows are located by labels. Very small total discrepancies consistent with Excel's approximately 15-digit cached numeric precision are tolerated (maximum of 1 rial and `abs(source_total) × 10^-14`); material differences remain warnings. Missing summary percentages remain null and are not fabricated.

One validated revision per report date enters analytics; alternate revisions remain in the library. Hidden duplicate sheets are excluded. Exact symbol suffixes and names are not merged, and missing observations are not assumed to be zero. Database chart values use floating-point numbers after Decimal-based source checks; original workbooks retain the full stored precision.

Net individual purchases measure an ownership transfer, not new cash entering the exchange or a return forecast. The detailed tables contain mixed instrument types. Their aggregate values are not equity-only totals, and the narrower summary percentages must not be applied to the full detailed-table total. Investor counts, closing-price returns, sector maps, and valuation histories require additional sources.

## Files and operations

```text
app.py                         HTTP server and query API
web/static/                    HTML, CSS, JavaScript (no build step)
scripts/download_reports.py    Resumable whole-archive downloader
scripts/index_reports.py       Incremental SQLite ingestion
scripts/analyze_reports.py     Decimal-based workbook extraction/checks
scripts/sync_archive.py         Download + index orchestration
data/raw/                      Original Excel files
data/download-manifest.json    Attachment IDs, source URLs, file paths, SHA-256
data/report-catalog.json       Source entries, including non-Excel reports
data/download-status.json      Latest download progress
data/download-errors.json      Failed source pages/attachments
data/archive.sqlite3           Web app database (WAL mode)
reports/                       Original 20-report research note and CSV exports
```

The files in `reports/` are the earlier **20-report snapshot**, not full-archive exports. Use the web app's CSV buttons for current indexed history. The legacy batch analysis script reads every workbook into memory; use the incremental indexer for the full archive.

The app's indexer skips already-parsed content hashes. `--retry-errors` retries warning/unsupported files with the current parser; bumping `PARSER_VERSION` reindexes after parser changes. `--watch` checks for new downloads every 8 seconds. Run `app.py --no-index-watch` if you manage indexing separately. App logs from UI refreshes are in `data/sync.log`; indexer logs are in `data/index.log`.

To back up the database while the app runs, use SQLite's backup API rather than copying only the main database file while WAL writes are active. Original workbooks and the manifests are sufficient to reconstruct it.

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile app.py scripts/*.py
node --check web/static/app.js
```

The regression suite covers multipage discovery, duplicate attachments/content, filename revisions, preserving previous downloads on a limited run, retrying failures, repairing damaged files, historical date formats/shifted summaries, known sample figures, and consistent date filtering/search/export queries. Browser checks cover desktop/mobile layout, report pagination, symbol search/history, all chart modes, custom/empty dates, filtered downloads, and server-error handling.
