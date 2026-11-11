---
name: iran-market-data
description: Use when inspecting Iranian financial files, mapping Persian fields or instrument identifiers, joining TSETMC and CODAL data, or handling Jalali dates, units and corporate actions.
---

# Iranian market data reference

Preserve the observation before interpreting it. Identity, units, source scope and availability time are independent data fields.

## Inspection steps

1. Inventory every workbook sheet, including hidden sheets, merged headings, cached formula results, errors, units, dates and duplicated tables. Identify report family before applying a daily schema. Never evaluate untrusted workbook macros or external links.
2. Store original bytes/hash, report/attachment IDs, original text and URLs. Capture exact cell text, sheet/row/cell, heading group, parser version and validity reason.
3. Normalize Arabic/Persian Yeh/Kaf, locale digits and date separators for matching; retain original spelling and ZWNJ in presentation. Missing, error, zero and unmatched identifier remain different states.
4. Map investor role, buy/sell action and amount/percentage using explicit headings and merged ranges. A redundant header can corroborate a missing heading; numerical magnitude alone cannot assign ownership or units.
5. Resolve instruments with dated TSETMC `insCode`, `instrumentID`, `cIsin`, venue/board/type and source-symbol mappings. Check valid-time coverage and ambiguity. Preserve suffixes and company-versus-security distinctions.
6. Reconcile amounts per row and measure, footer and source scope. Keep independently usable value/volume fields; exclude only metrics whose required inputs fail.

## Semantic quick reference

| Observation | Meaning |
|---|---|
| Source value / matching quantity | Execution VWAP for that population, not official close or holder cost basis |
| `pClosing` / last trade | Separate source-reported price concepts; verify field definitions and adjustment status |
| Rial / toman | 10 rial = 1 toman; 10^13 rial = 1 trillion toman |
| Visible percentage / hidden input | Can be 0–100 versus 0–1; require declared scale |
| Session date / publication / first observed | Different clocks; retain raw calendar/timezone and normalize only with evidence |
| Client count / trade count | Distinct fields; neither automatically means distinct beneficial owners |
| Adjusted price | Vendor transformation; not automatically a dividend-reinvested total return |

## Enrichment and failure checks

Use official-host TSETMC observations and original CODAL versions; use operative SEO/CMR/TSE/IFB documents for rules. Community wrappers help discover fields but do not establish definitions or historical coverage. Check stale/default API responses, corporate-action jumps, renamed/delisted instruments, revisions and effective-date gaps.

Example: `وبملت1` and `وبملت2` stay separate unresolved observations until a dated master proves each relationship. A blank hidden amount cannot override an explicit primary zero or become a guessed zero.

## Output

A field dictionary, source-to-canonical mapping, unit/calendar conversion record, duplicate/quality report, unresolved identity list and enrichment gap list. Canonical records retain exact amounts; display approximations are labeled.

Project references: `docs/research/dataset-inventory.md`, `docs/research/data-gap-analysis.md`, `docs/research/sources-market-structure.md`.
