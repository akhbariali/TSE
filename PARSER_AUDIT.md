# Workbook parser and selective-data audit

Audited 11 November 2026 using all 794 distinct downloaded workbook contents, parser version 5. No original workbook was modified or committed.

| Source status | Workbook count | How its data is used |
| --- | ---: | --- |
| No warnings | 351 | Complete value tables and checked instrument rows |
| Warning, complete value table | 419 | Market charts and symbol analysis; source warnings stay visible |
| Warning, partial value table | 21 | Only checked value rows enter symbol analysis |
| Warning, contradictory value table | 1 | Identified fields and checked volume data remain available in Parsed CSV |
| Non-daily report | 2 | Original download; daily ownership metrics unavailable |

There are **770 workbooks eligible for market totals**, representing **769 distinct chart dates** after revision selection. **791 workbooks have checked value rows**, representing **790 symbol-analysis dates**. The index retains **594,184 instrument observations**, including **591,266 rows with checked value flows**. Revision selection prevents identical dates from being counted twice in analytics.

The source-status counts remain 351 without warnings, 441 with warnings, and 2 unsupported. Their usability has changed: 440 warning files now contribute checked value data. Warnings describe source discrepancies and do not automatically exclude an entire workbook.

## Reading columns by meaning

The parser recognizes symbol, investor role, buy/sell action, and value/volume from actual headings, including merged groups and Persian/Arabic letter variants. It found **375 institutional-first workbooks**. Those investor roles are assigned from their labels. Missing or ambiguous investor fields remain null while other identifiable fields are retained; percentage data never substitutes for amounts. An omitted role subheading can be recovered only from an unambiguous redundant percentage-header pair.

379 files carry layout notes, including seven where secondary/template rows after the first total were excluded. `Summary - 14040222.xlsx` has 806 instrument rows; the old positional reader included its total and continued into a pasted table. The latest verified sample remains at 1,192 instruments, turnover of 596,948,215,456,567 rial, and individual net purchases of 74,101,817,413,833 rial.

## Deciding which metrics are usable

- Each identified amount must be finite and nonnegative. Volume quantities must also be integers. Missing and invalid cells remain null.
- A row supports value-flow metrics only if all four value amounts are available and combined purchases match combined sales within 1 rial. Volume has an independent exact-equality check.
- Missing or contradictory volume does not block checked value flows. VWAP requires both value and volume checks.
- A market value total requires all identified value rows to pass and corroborating investor footer totals, with only tiny Excel precision differences allowed. If there is no footer, the summary must corroborate the detail. Unresolved value-table errors or traded volume symbols missing from the value table prevent a completeness claim.
- A different summary total remains a warning when detailed rows reconcile to their investor footers. The app computes analytics from those detailed rows and retains source summary figures separately.
- Duplicate symbols are quarantined from derived metrics. The first observation remains inspectable with its ambiguity flagged.
- Partial-table sums never enter market charts. Checked rows from those tables can enter symbol rankings/history. Each analysis selects one suitable revision per date, preferring a complete table and then checked-row coverage.

These checks establish internal consistency and provenance. They do not independently verify the underlying exchange trades.

## Examples

- `KH - 021010.xlsx`: headers put institutions first. All 657 value rows pass and reconcile to the value footer. Detailed turnover is 61,300,456,302,695 rial; the summary says 61,300,043,191,695 rial. The detail is usable and the summary discrepancy remains visible.
- `KH- 14040813.xlsx`: detailed turnover is 209,407,433,502,345 rial; the summary states twice that amount. The app uses the reconciled detail and flags the summary.
- `KH- 14050319.xlsx`: 24 checked value rows and 906 checked volume rows. The 24 value rows enter symbol analysis; the incomplete value table cannot supply a market total. All 906 parsed observations remain available in CSV.
- `Summary - 14031029.xlsx`: all 739 value rows contradict combined purchases/sales and the value sell footer is zero. Derived value flows remain blank. Its 739 checked volume rows are retained for inspection/export.

The remaining two unsupported reports are a monthly report and a market review. They remain downloadable.

## Inspect and reproduce

The library shows **Validated**, **Usable · warning**, **Partial · symbol data**, or **Fields available** according to usability. Expand **Layout & validation details** for mappings, coverage, and source issues. **Parsed CSV** includes identified source amounts, original worksheet/row references, per-measure validity flags, and issues. Source amounts retain their exact cached decimal strings; derived/chart fields use numeric approximations after Decimal checks. A blank derived field means its required inputs did not pass.

```bash
python3 scripts/download_reports.py
python3 scripts/index_reports.py
python3 scripts/audit_reports.py
python3 -m unittest discover -s tests -v
```

The 38 tests cover synthetic Excel layouts, missing/ambiguous fields, summary disagreement with valid footers, contradictory rows, independent value/volume checks, duplicate symbols, incomplete-table protection, database migration/revision selection, and identical query/export filtering. An optional original-workbook regression checks the downloaded latest sample. Browser checks cover keyboard disclosure, partial-file status, Parsed CSV download, chart/ranking/history rendering, and desktop/mobile layouts in headless Chrome. Real-data checks confirm invalid value rows never enter symbol queries, unavailable metrics export as blanks, and SQLite integrity/foreign keys pass.
