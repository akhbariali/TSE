# TSE Market Archive

A local web app for browsing Tehran Securities Exchange market-performance workbooks and exploring individual/institutional ownership flows. **One username/password protects the web app.** No API key or external authentication service is required. The application uses Python 3.10+ and its standard library, with SQLite for incremental storage. The downloader's process locks use `fcntl` (Linux/macOS).

## Run the app

```bash
cd /path/to/TSE
python3 scripts/configure_login.py --username admin
python3 app.py --port 8000
```

Open **http://127.0.0.1:8000**. The existing downloaded files and database are ready to use. The server starts a lightweight background indexer that notices new downloads; it does not automatically start a network download. The UI has no external font, chart-library, or CDN dependency.

To listen on another interface, use `--host 0.0.0.0`. Pages, both market APIs, original downloads, exports, and archive refresh require a signed-in session. Use HTTPS for public access. Nginx deployment details are below.

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
- Net transfers, transfer-to-turnover ratios, observed-day buying persistence, and symbol history with average traded prices and investor-category purchase VWAPs. Average price (rial) is trading value divided by volume, weighted by volume across the selected period in rankings; it is not a closing or live price. Zero-volume prices are unavailable.
- Searchable report library with original Excel downloads, publication dates, TSE source links, file sizes, and validation/revision status.
- CSV exports that respect the selected dates and symbol-table filters. Amount fields ending in `_rial` use rials, not the trillion-toman display unit.
- Archive progress and data methodology, with explicit analysis exclusions.

The interface currently uses English, with Persian source labels/symbols retained and Solar Hijri report dates. Gregorian publication dates are explicitly labeled. The original source files are authoritative.

## Data quality and interpretation

After parser version 4 recovery, the local archive has **304 fully validated workbooks, 487 partial workbooks, and 3 unsupported workbooks** (794 distinct workbook contents). The parser now retains usable value rows in partial reports. Partial reports enter analytics with explicit coverage warnings; unsupported files remain downloadable and searchable. Historical examples include mismatched value/volume symbol sets, source totals that do not reconcile with detailed rows, and monthly report layouts outside the daily parser. Review the exact issue in the library before relying on a file.

Dates are normalized from compact, slash-separated, dash-separated, and Persian-digit formats. Shifted daily summary rows are located by labels. Very small total discrepancies consistent with Excel's approximately 15-digit cached numeric precision are tolerated (maximum of 1 rial and `abs(source_total) × 10^-14`); material differences remain warnings. Missing summary percentages remain null and are not fabricated.

One revision per report date enters analytics, preferring fully validated reports over partial reports; alternate revisions remain in the library. Hidden duplicate sheets are excluded. Exact symbol suffixes and names are not merged, and missing observations are not assumed to be zero. Database chart values use floating-point numbers after Decimal-based source checks; original workbooks retain the full stored precision.

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

### Partial report recovery

Parser version 4 resolves ownership columns from their two-level Persian headings, including shifted columns. Value rows require finite nonnegative amounts and balanced purchase/sale totals. Invalid or ambiguous duplicate value rows are excluded. Missing or invalid volume leaves volume-derived fields and prices unavailable while retaining valid value flows. Value rows that exactly copy their nonzero volume amounts are treated as suspect and excluded.

Partial reports retain published totals, reconciliation gaps, excluded symbol/reason pairs, and missing-volume symbols. The report library exposes extraction details. Charts and exports use retained rows only; partial totals are incomplete market coverage. Period average prices use only observations with valid positive volume. Original files are preserved. Changing the parser version causes the indexer to reprocess cached workbooks on its next start.

## Routine archive updates and recovery

Use **Update archive** in the app, or run:

```bash
python3 scripts/sync_archive.py
```

Every newly downloaded or revised workbook automatically goes through the same extraction, column detection, accounting checks, and partial-row recovery described above. This applies to all files in the download manifest, without a separate manual cleanup step. Existing unchanged workbooks already indexed by the current parser are reused. With the app running, its watch indexer handles new files; the sync command may report that another indexer owns the lock, which is expected.

After updating, wait for indexing to finish and review **Report library → Partial · retained valid rows → Extraction details**. Check excluded symbols and reconciliation gaps before using partial totals. Original workbooks remain untouched.

When improving extraction rules, increment `PARSER_VERSION` in `scripts/index_reports.py`, stop the app to release its indexer lock, then run:

```bash
python3 scripts/index_reports.py
python3 app.py --port 8000
```

The version change reprocesses **every workbook**, including previously validated files. To retry only partial/warning/unsupported workbooks without a version change, stop the app and run `python3 scripts/index_reports.py --retry-errors`, then restart the app. Never remove the database or original downloads to force a retry. Run the verification commands above after parser changes.

In symbol history, choose **Average price** to chart daily traded value ÷ volume in rials. Unavailable prices appear as gaps; hover points for dates and prices. The selected report window applies to both the chart and table.

Symbol history defaults to **Both**: net-transfer bars on the left scale (trillion toman) and a blue average-price line on the right scale (rials). Hover a date for both values. Missing prices leave gaps while net-transfer bars remain visible. Each series uses its own scale.

## IFB (Iran Fara Bourse): separate archive

Use **Switch to IFB** at the top of the sidebar to open IFB, and **Switch to TSE** to return. IFB uses a red theme and TSE uses blue; the same navigation links follow the selected market. The **IFB** overview, report library, symbol explorer, and methodology pages use an independent database at `data/ifb/archive.sqlite3`. IFB observations are never added to TSE totals, rankings, history, exports, or downloads. Identical symbol labels in the two markets remain separate. The selected section's **Update archive** button updates only that market.

Source: [IFB periodical reports](https://www.ifb.ir/datareporter/periodicalreport.aspx). The IFB updater submits the daily trading-statistics filter, follows ASP.NET pagination (including subsequent pager groups), and downloads the ownership and price workbooks. The default scans all exposed daily pages; `--limit 20` requests a recent sample without removing older files:

```bash
python3 scripts/ifb_archive.py
python3 scripts/ifb_archive.py --limit 20
```

Ownership workbooks provide purchase/sale value, volume, and investor counts. Columns are identified from the three-level headers. Merged market/submarket labels are carried forward; subtotal and summary rows never become symbols. Blank investor cells in this IFB export layout represent zero; purchase/sale balance and available row totals are checked. Invalid value rows are excluded, while missing/invalid volume leaves volume-derived fields unavailable. Multi-day ownership reports are excluded from daily history to prevent overlapping periods.

Price workbooks are stored as **Price reference** reports and do not add ownership sessions or turnover a second time. Closing and last-trade prices are joined only to the exact IFB symbol and report date. The price workbook's comparison-start date is not the trading date. Average traded price remains trading value ÷ volume; the workbook's published mean is preserved separately because its methodology can differ. Price references can cover fewer symbols than ownership reports; reconciliation gaps are shown in extraction details. Missing prices stay blank.

IFB files, download status, errors, catalog, logs, and manifest live under `data/ifb/`; original Excel files are retained by hash in `data/ifb/raw/`. The two manually supplied inspection files have been removed from the repository root after archiving their usable data. No Excel binaries are committed.

To import additional IFB samples locally:

```bash
python3 scripts/ifb_archive.py --import-files /path/to/report.xlsx
```

On every update, the IFB indexer checks cached files before downloading new ones. After changing IFB extraction rules, increment `PARSER_VERSION` in `scripts/ifb_archive.py`; the next update reprocesses all archived IFB workbooks. `--retry-errors` reprocesses cached workbooks without a version bump. Repeated downloads reuse report IDs and content hashes; revisions remain archived, and one ownership revision per date enters analytics. A dedicated IFB lock prevents concurrent update writers. Interrupted/failed downloads are retried on the next update. Review **IFB → Data & methodology** and the report library for coverage and exclusions.

## Server deployment

The app is deployed from Git branch **develop** to `/opt/tse` on `94.184.25.127`. Python 3 and its standard library are sufficient. The systemd service runs as the unprivileged `tse` user, starts on boot, and restarts on failure. Git code is managed by root; only `data/` is writable by the service. TSE and IFB databases and original workbooks remain outside Git under that directory.

Current address: **http://94.184.25.127:8000**. The reverse proxy is deferred; ports 80/443 remain available for other services. Bind settings live in `/etc/tse.env`:

```text
TSE_HOST=0.0.0.0
TSE_PORT=8000
```

After committing and pushing changes to `develop`, deploy with:

```bash
ssh root@94.184.25.127 tse-update
```

The update command fetches `origin/develop`, verifies a fast-forward, tests the incoming commit in a temporary directory, updates the checkout, restarts the service, and checks both market APIs. It preserves archived data and stops when tracked files have local edits. Configuration sources are in `deploy/tse.service`, `deploy/tse-update`, and `deploy/tse.env.example`; installed copies are `/etc/systemd/system/tse.service` and `/usr/local/bin/tse-update`. If those files change in Git, install the new copies explicitly and run `systemctl daemon-reload` before restarting.

Useful server commands:

```bash
systemctl status tse
journalctl -u tse -n 100 --no-pager
systemctl restart tse
git -C /opt/tse rev-parse --short HEAD
```

When the reverse proxy is added, change `TSE_HOST` to `127.0.0.1`, restart `tse`, and proxy the chosen domain to `127.0.0.1:8000`. The app requires a single-account login. Until HTTPS is active, use an SSH tunnel rather than submitting credentials over public HTTP. Back up each database through SQLite's backup API and retain the manifests and raw workbooks. Never copy a live database without its WAL state.

### Nginx and HTTPS for tse.talebidir.shop

Nginx now routes `tse.talebidir.shop` on port 80 to `127.0.0.1:8000`, preserving the original Host header for archive-refresh requests. Its site configuration is `/etc/nginx/sites-available/tse`; `deploy/tse.nginx.conf` is the HTTP bootstrap template. Certbot will extend the installed configuration with HTTPS and HTTP-to-HTTPS redirects; do not overwrite that generated configuration with the bootstrap template afterward.

At setup time, public DNS returned `SERVFAIL` because the delegated ParsPack nameservers (`ns1.parspack.co` through `ns4.parspack.co`) refused queries. Nginx was verified with the domain's Host header, but a trusted certificate cannot be issued until public DNS works. Confirm the ParsPack domain/zone is activated and that the active DNS service's nameservers match those configured at the registrar. The A record must resolve to `94.184.25.127`; avoid an AAAA record unless IPv6 is configured on this server.

`tse-https.timer` checks every 15 minutes. Once both Google and Cloudflare DNS return the server address, `/usr/local/bin/tse-enable-https` obtains a Let's Encrypt certificate, enables redirects, tests both market APIs, binds the application to loopback only, and disables the bootstrap timer. Existing access via port 8000 remains available until HTTPS succeeds. Certbot's separate `certbot.timer` handles certificate renewal afterward. Certificate registration currently has no notification email.

To trigger setup immediately after fixing DNS:

```bash
ssh root@94.184.25.127 systemctl start tse-https.service
ssh root@94.184.25.127 journalctl -u tse-https.service -n 30 --no-pager
```

Other future services can have their own Nginx `server_name` blocks on the same ports 80/443. This site's configuration does not claim those domains.

## Single-account login

Create or change credentials with `python3 scripts/configure_login.py --username admin`. The password is entered interactively, must have at least 12 characters, and is stored as a salted PBKDF2-SHA256 hash with 600,000 iterations. The default file is ignored by Git at `data/auth.json`; `TSE_AUTH_FILE` can override its location. The app refuses to start without valid credentials.

The deployed service uses `/etc/tse-auth.json` (root-owned, group `tse`, mode 0640), configured in `/etc/tse.env`. To change the server account:

```bash
ssh -t root@94.184.25.127 'cd /opt/tse && python3 scripts/configure_login.py --username admin --output /etc/tse-auth.json && chown root:tse /etc/tse-auth.json && chmod 0640 /etc/tse-auth.json && systemctl restart tse'
```

Sessions expire after 12 hours and are revoked on sign-out or server restart. Session cookies use HttpOnly and SameSite=Strict, plus Secure behind the trusted loopback HTTPS proxy. Repeated login attempts are throttled. All application data and update actions require authentication; only the login page, its stylesheet, and the data-free `/healthz` liveness endpoint are public. Nginx must overwrite `X-Forwarded-Proto` and `X-Real-IP` as in the supplied configuration.

While DNS/HTTPS is pending, access privately with:

```bash
ssh -N -L 8080:127.0.0.1:8000 root@94.184.25.127
```

Then open `http://localhost:8080`. The SSH connection encrypts the public-network traffic. Once the certificate is active, use `https://tse.talebidir.shop` directly.

### DNS diagnosis

Check independently of your browser or local DNS cache:

```bash
dig @1.1.1.1 tse.talebidir.shop A
dig @8.8.8.8 tse.talebidir.shop A
dig @ns1.parspack.co talebidir.shop SOA +norecurse
```

The first two should return status NOERROR and A address `94.184.25.127`. At setup, both returned SERVFAIL and direct authoritative queries returned REFUSED. That indicates a DNS service/delegation problem rather than an application or browser problem. The `.shop` registry delegates this domain to `ns1.parspack.co` through `ns4.parspack.co`. Compare these with the exact nameservers assigned to this domain by the ParsPack CDN dashboard; change registrar delegation if they differ. If they match, ask ParsPack to activate/repair the DNS zone and include the authoritative REFUSED responses. Confirm the saved `tse` A record is DNS-only, points to the server, and has no conflicting CNAME/AAAA record. The private dashboard requires your account session and cannot be inspected through a public URL alone.
