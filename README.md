# TSE Market Archive

A local web app for browsing Tehran Securities Exchange market-performance workbooks and exploring individual/institutional ownership flows. **No login, API key, or external service is required.** The application uses Python 3.10+ and its standard library, with SQLite for incremental storage. The downloader's process locks use `fcntl` (Linux/macOS).

## Run the app

```bash
cd /path/to/TSE
python3 app.py --port 8000
```

Open **http://127.0.0.1:8000**. Downloaded workbooks and the database are local, ignored files. On a fresh clone, run the download and indexing commands below to populate the archive. The server starts a lightweight background indexer that notices new downloads; it does not automatically start a network download. The UI has no external font, chart-library, or CDN dependency.

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
- Archive progress and data methodology, with field and row validity explained.

The interface currently uses English, with Persian source labels/symbols retained and Solar Hijri report dates. Gregorian publication dates are explicitly labeled. The original source files are authoritative.

## Data quality and interpretation

The 794-workbook audit found **351 files without warnings, 441 with warnings, and 2 non-daily reports**. A warning no longer excludes an entire file. Of the warning files, **419 have complete, reconciled value tables** usable in market charts, **21 have checked value rows** usable in symbol analysis, and **1 retains volume fields** while its contradictory value rows cannot produce value flows. After selecting one suitable revision per date, there are **769 market chart dates and 790 symbol-analysis dates**.

A value flow requires all four correctly identified, finite, nonnegative value amounts and matching combined purchases/sales within 1 rial. Volume is checked independently, using integer quantities and exact purchase/sale equality. VWAP requires both checks. Market totals require every identified value row to pass, no unresolved value-table errors, and corroborating investor footer totals (or the summary when no footer exists). A disagreeing summary remains visible while a reconciled detailed table can be used. Partial tables contribute only their checked rows to symbol analysis; partial sums are never shown as full market totals.

Columns are detected from actual symbol, buy/sell, investor-role, and volume/value headings, including Persian/Arabic letter variants and English aliases. Reordered columns, institutional-first reports, shifted headers, renamed worksheets, and merged heading groups are supported. A missing investor subheading is recovered only when an explicit, unambiguous percentage-header pair corroborates its identity; percentages never substitute for trading amounts. Missing or conflicting investor headings make only those fields unavailable; other clearly identified fields are retained. A table whose measure or symbol identity cannot be resolved remains unsupported. Missing company names are allowed; missing or invalid numeric cells are never assumed to be zero.

The first labeled total ends the instrument table, even when it has a numeric row index or is labeled in the index column. Subsequent pasted/template rows are excluded. Duplicate symbols retain the first source observation for inspection, are flagged as ambiguous, and cannot produce derived metrics. Every parsed investor subtotal is checked against its footer when available, then the combined rows are reconciled against the summary. Original Excel files are never rewritten. Expand **Layout & validation details** in the report library to inspect column mappings, usable-row counts, adjustments, and the complete issue list. **Parsed CSV** exports identified source amounts with exact stored decimal text, worksheet/row references, validity flags, and row issues. Derived fields are blank when their inputs are missing, ambiguous, or contradictory. Chart/derived CSV values use numeric approximations after Decimal checks.

Dates are normalized from compact, slash-separated, dash-separated, and Persian-digit formats. Shifted summary rows and moved total columns are located by labels. Very small total discrepancies consistent with Excel's approximately 15-digit cached numeric precision are tolerated (maximum of 1 rial and `abs(source_total) × 10^-14`); material differences remain warnings. Missing summary percentages remain null and are not fabricated.

One suitable revision per date is selected independently for market and symbol analytics, preferring a complete value table, then greater checked-row coverage, then publication recency. Market selection prefers a report without warnings when available. Alternate revisions remain in the library. Hidden duplicate sheets are excluded. Exact symbol suffixes and names are not merged, and missing observations are not assumed to be zero. Database chart values use floating-point numbers after Decimal-based source checks; original workbooks retain the full stored precision.

Net individual purchases measure an ownership transfer, not new cash entering the exchange or a return forecast. The detailed tables contain mixed instrument types. Their aggregate values are not equity-only totals, and the narrower summary percentages must not be applied to the full detailed-table total. Investor counts, closing-price returns, sector maps, and valuation histories require additional sources.

## Files and operations

```text
app.py                         HTTP server and query API
web/static/                    HTML, CSS, JavaScript (no build step)
scripts/download_reports.py    Resumable whole-archive downloader
scripts/index_reports.py       Incremental SQLite ingestion
scripts/analyze_reports.py     Decimal-based workbook extraction/checks
scripts/workbook_layout.py     Header detection and safe table normalization
scripts/audit_reports.py       Indexed validation/layout audit (JSON)
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
python3 scripts/audit_reports.py
node --check web/static/app.js
```

The 38-test regression suite covers selective field retention, missing value/volume tables, row contradictions, duplicate-symbol quarantine, partial-data query/export consistency, revision selection, and multipage discovery, duplicate attachments/content, filename revisions, preserving previous downloads on a limited run, retrying failures, repairing damaged files, historical date formats/shifted summaries, known sample figures, and consistent date filtering/search/export queries. Browser checks cover desktop/mobile layout, report pagination, symbol search/history, all chart modes, custom/empty dates, filtered downloads, and server-error handling.

## Version control

The original app is preserved on `main` (commit `9629a31`). The parser corrections are on `fix/resilient-workbook-layouts`. All Excel formats, downloaded data/manifests, SQLite databases, generated reports, logs, and local environments are excluded by `.gitignore`. A fresh clone recreates local data with the downloader and indexer. See [PARSER_AUDIT.md](PARSER_AUDIT.md) for the complete archive audit and remaining limitations.
