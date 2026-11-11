# Dataset inventory and current architecture

Inspected **2026-11-11**, repository `/home/ali/Documents/GitHub/TSE`, application revision `020bfbd`. This is an observation of local files, not a claim of complete Iranian exchange coverage. No source file was changed.

## Archive coverage

| Item | Observed |
|---|---:|
| Catalog entries / pages from the existing download | 802 / 41 |
| Excel attachments / distinct byte contents | 797 / 794 |
| Ordinary daily ownership workbooks | 792 |
| Other report families | 1 monthly, 1 market review |
| Sheet instances inventoried, including hidden sheets | 4,895 |
| Retained symbol/date/workbook observations | 594,184 |
| Checked value-flow observations | 591,266 |
| Checked volume observations | 594,167 |
| Distinct raw symbol labels across all retained observations | 10,739; **not** 10,739 companies |
| Market-eligible workbook contents / selected dates | 770 / 769 |
| Workbooks with checked value rows / selected symbol dates | 791 / 790 |
| Selected date range | 1402/04/03–1405/08/19 |

Source checks: existing manifest/catalog and read-only SQLite queries; `python3 scripts/audit_reports.py` reproduces the core coverage counts. Original XLSX bytes and local audit evidence remain ignored under `data/`.

**Schema inspection coverage:** every sheet's name/state, XML dimensions, cached cells in its first 60 rows, and text labels in its first 30 rows were inspected across all 794 files. The entire sample workbook's cached rows were inspected. The existing parser's archive-wide numeric validation covers the daily ownership tables. This is not an exhaustive validation of every cell in the non-daily or auxiliary sheets. XML dimensions include formatting and are not trusted as data-row counts.

## Sample identity and timing

`data/raw/KH - 14050819.xlsx` is byte-identical to `/home/ali/Downloads/KH - 14050819.xlsx`.

- SHA-256: `1ef908416e6103d35d563efa19b2edd5bbd372cee6bbe6e02d9ebcecffac6b8a`.
- Size: 2,010,052 bytes; report ID `102576`.
- Trading date text: `1405/08/19`; source effective date: `2026-11-10T00:00:00`.
- Source publication text: `2026-11-11T09:35:28.3544677`, **without an offset**. The source timezone and amendment semantics remain unverified. This timestamp cannot yet be promoted to a trusted UTC availability time for a backtest.
- [Original report page](https://www.tse.ir/delivery-detail?id=102576); [source attachment](https://webgw.tse.ir/File/Download/2206a4bb-1cc4-4295-82b0-f8f914a14ea5).

The title/trading date is a different concept from publication, download, and indexing time. Current `indexed_at` does not establish when the data was first publicly available.

## All seven sample sheets

| Sheet | State | Cached content and purpose | Analytical treatment |
|---|---|---|---|
| به نام خدا | Hidden | No cached nonempty cell rows; presentation can be drawing-based | No numerical source |
| شناسنامه | Visible | No cached nonempty cell rows | No numerical source; absence of cached cells does not prove the rendered page is empty |
| خلاصه بازار | Visible | 14 nonempty cached rows, rows 6–25; total volume/value, shares-and-rights investor percentages, top-three panels | Summary and scoped cross-checks; do not add top-three panels to detailed totals |
| تغییر مالکیت براساس حجم | Visible | 1,197 nonempty cached rows; 1,192 instruments plus headings/footer; 11,939 formulas; five cached error cells in helper areas | Primary volume table, using explicit investor headings |
| تغییر مالکیت براساس ارزش | Visible | 1,196 nonempty cached rows; 1,192 instruments plus headings/footer; 11,934 formulas | Primary value table |
| ص1 و 2 | Hidden | 2,402 nonempty cached rows through row 2,407; summary/top-three and raw/template tables | Auxiliary overlapping input/template; no automatic substitution |
| ص 3 | Hidden | 1,196 nonempty cached rows through row 1,198; value raw/template data | Auxiliary overlap; no automatic substitution |

Of the 1,192 symbols, **829** have all four hidden raw amount cells explicitly present and exactly matching each corresponding visible primary table; **363** have at least one omitted hidden raw amount cell while the visible primary table contains explicit values, often zero. This is evidence of overlap and different blank conventions, not permission to treat arbitrary missing cells as zero. No mismatching complete four-cell pairs were found in that sample comparison.

Cached results are read without evaluating Excel formulas. Formula counts and helper errors are not themselves instrument-data validity failures. Audit metadata must distinguish `t="e"`, missing cached values, zero, and failed reconciliation.

## Primary daily table fields

The sample has symbol header in B, company in C, amount columns D/E/H/I, percentage columns F/G/J/K. These positions **vary historically** and must not be used as a universal schema.

| Source meaning | Canonical field | Unit / interpretation |
|---|---|---|
| نماد / کد فارسی نماد | `source_symbol` | Preserve exact Persian spelling and suffix; no verified stable security key |
| نام شرکت | `source_company_name` | Descriptive label; can name a fund or other instrument |
| حجم خرید حقیقی / حقوقی | `retail_buy_volume`, `institutional_buy_volume` | Shares or source instrument units; integer quantities |
| حجم فروش حقیقی / حقوقی | `retail_sell_volume`, `institutional_sell_volume` | Same source-unit caveat |
| ارزش خرید حقیقی / حقوقی | `retail_buy_rial`, `institutional_buy_rial` | Rial amounts, interpreted consistently with source totals |
| ارزش فروش حقیقی / حقوقی | `retail_sell_rial`, `institutional_sell_rial` | Rial amounts |
| درصد خرید / فروش | Percentage labels and cached values | Presentation scale differs: visible tables commonly 0–100, hidden inputs commonly 0–1; do not infer a common scale silently |
| ردیف | Source row ordinal | Not a security identifier; totals sometimes have a numeric ordinal |
| کنترلی مهم / جمع کل helper cells | Source diagnostics | Not instrument fields or additional transactions |

The summary top-three panels explicitly use **million shares** and **billion rial**; the monthly report also uses scaled units. The app display uses **trillion toman**, with 10 rial = 1 toman and 10^13 rial = 1 trillion toman. Store source units and conversion rules explicitly.

**Verified daily totals for the sample:** 1,192 rows; combined purchase volume 52,177,504,941; detailed turnover 596,948,215,456,567 rial; individual net purchases 74,101,817,413,833 rial. These are existing regression anchors, not a price or return series.

## Archive sheet families and extra data

Each of the 792 daily workbooks has the four visible sheets شناسنامه, خلاصه بازار, and the two ownership tables. Auxiliary `BI` sheets occur **666** times (599 visible, 67 hidden). `ص1 و 2` occurs 126 times; `ص 3` 126 times. `به نام خدا` occurs 788 times. These often combine summary/raw tables and duplicate information; a sheet's visibility alone does not make it an independent observation.

The two other families reveal additional opportunities:

- `Monthly - 021030 - e.xlsx`: ten sheets including `final`, `کل`, `به تفکیک بازار`, `شاخص`, `نمودار شاخص`, `آمار دوره ای` and control sheets. Contains dated period boundaries, market/segment totals, trade counts, trading days and index-period observations, commonly in million/billion units. A single period report does not provide a full daily return series.
- `Negahi-020612 - e.xlsx`: fourteen sheets including `شاخص`, `بازارها`, `خرد`, `بلوک`, `عمده`, `ناظر`, `عملیات` and raw helpers. Observed labels include market-segment trade counts/volume/value, ordinary shares versus rights, block/major symbols, supervisor-message text/subject/time, and next-day halt reasons. These are sparse historical observations with separate scope. Trade counts are **not participant counts**.

Neither family is supported by the present daily parser. They should receive explicit report-family adapters after the first milestone, rather than be forced into daily ownership rows. Their hidden raw sheets and formulas require a separate validation pass before use.

## Data currently absent from the daily analysis contract

Not verified as a usable longitudinal daily dataset: OHLC/official close/last-trade prices; corporate-action-adjusted total returns; participant counts with authoritative meanings; dated sector/type/venue mappings; market cap/free float/outstanding units; order books, queue priority or execution prints; historical limits/base volumes/halts; financial statements, valuation denominators, dividend cash flows; fee/settlement regimes; inflation/FX/risk-free benchmarks.

The source contains funds and multiple suffixes for the same company. Name keywords may suggest classification for review but cannot certify an equity universe. An investor-category purchase VWAP from value/quantity is not a close, total-return price, or average purchase cost of every existing holder.

## Existing system and reuse boundaries

| Module | Current job | Proposed treatment |
|---|---|---|
| `scripts/download_reports.py` | All-page discovery, attachment/hash deduplication, resumable atomic downloads | Reuse; later extend provenance with append-only observations |
| `scripts/workbook_layout.py` | Header/merged-cell detection, text normalization, independent field parsing | Reuse; preserve source labels and diagnostic scopes |
| `scripts/analyze_reports.py` | Decimal checks, row/measure eligibility, existing flow/VWAP metrics | Reuse verified behavior; gradually separate pure metric functions |
| `scripts/index_reports.py` | SQLite canonical views and approximate numerical serving columns | Reuse for serving; add immutable analytical observations and as-of selection before predictive work |
| `scripts/audit_reports.py` | Source-state/usability audit | Reuse as ingestion acceptance evidence |
| `app.py` and `web/static/` | No-login browsing, market/symbol scopes, charts, downloads and CSV | Keep operating; new metrics arrive through a later approved adapter |
| `tests/` | 38 existing regression cases at the start of this research | Extend using independent arithmetic fixtures and property/invariant checks |

Current storage retains exact parsed amounts in `flows.source_data` JSON but uses REAL columns for charting. Current revision views select a suitable revision using all currently downloaded versions; they are **not point-in-time historical universes**. Same-byte republishing can update the one workbook's publication metadata. The retained source catalog/attachment manifest helps provenance but is not an immutable availability ledger. These are critical research-storage requirements, not reasons for a wholesale application rewrite.

## Reproduction and evidence limits

- `python3 scripts/audit_reports.py`: indexed scope/usability.
- Read `xl/workbook.xml`, workbook relationships, shared strings, and worksheet XML with `zipfile`/ElementTree: sheet metadata, cached values, formulas and source headers.
- Ignored local observations: `data/schema-inventory.json`, `data/schema-inventory-summary.json`, `data/sample-all-sheets.json`, `data/sample-schema-inventory.json`.

The schema inventory was produced by a temporary read-only probe; it is not yet a maintained user-facing feature. The first milestone plan includes a versioned single-workbook observation adapter, provenance exports and numerical acceptance tests; a maintained archive-wide schema inventory tool remains a later engineering task. No prices, participants, sectors or returns were invented from these sheets.
