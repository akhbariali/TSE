# Workbook parser audit

Audited 11 November 2026 using all 794 distinct downloaded workbook contents. No source workbook was modified or committed.

| Status | Original parser | Header-based parser |
| --- | ---: | ---: |
| Validated | 345 | 351 |
| Warning, excluded from analytics | 443 | 441 |
| Unsupported | 6 | 2 |

All 345 previously validated files remain validated. Three warning files and three unsupported files now validate; one unsupported file now parses with source warnings. The remaining two unsupported workbooks are a monthly report and a market review, rather than daily ownership reports.

The audit found 375 institutional-first workbooks. Fixed-position extraction had assigned their investor roles incorrectly. The new parser uses the explicit investor labels for both value and volume. This matters even for files that remain excluded because their source totals disagree.

379 files carry layout notes, including seven where secondary/template rows after the first total were excluded. For example, `Summary - 14040222.xlsx` now validates with 806 instruments; the old reader included the total as an instrument and continued into a pasted table. The verified latest sample still has 1,192 instruments, turnover of 596,948,215,456,567 rial, and individual net purchases of 74,101,817,413,833 rial.

## Remaining discrepancies

All 441 warning workbooks have detailed turnover and volume totals that disagree with the summary. Three also have different value/volume symbol sets. There are 18 investor-footer mismatch occurrences and 1,211 per-symbol buy/sell mismatch occurrences across the warning files; these counts overlap, and most per-symbol failures are concentrated in two files. These are retained as source discrepancies, with exact diagnostics in the report library.

Examples:

- `KH- 14040813.xlsx`: detailed turnover is 209,407,433,502,345 rial; the summary states 418,814,867,004,690 rial. The parser excludes the footer rather than doubling the instruments to force agreement.
- `KH- 14050319.xlsx`: 882 symbols exist only in the volume table. Missing value rows are not reconstructed.
- `Summary - 14031029.xlsx`: the value-table sell footer is zero despite populated instrument rows, and hundreds of instrument buy/sell amounts disagree.

No ambiguous or missing trading amounts are filled with invented zeroes. Missing company names do not prevent symbol-based extraction. Only validated reports enter web analytics. Source files remain available for every status, and the layout disclosure shows the interpreted columns and all warnings.

## Reproduce

```bash
python3 scripts/download_reports.py
python3 scripts/index_reports.py
python3 scripts/audit_reports.py
python3 -m unittest discover -s tests -v
```

The 24 regression tests include synthetic Excel workbooks generated in temporary directories, so no binary fixtures need to be tracked. The optional original-workbook regression runs when the downloaded latest sample is present. Browser checks covered the expandable diagnostics with keyboard input, a recovered report, original Excel download, overview rendering, and desktop/mobile layout in headless Chrome. The daily CSV excludes internal layout metadata.
