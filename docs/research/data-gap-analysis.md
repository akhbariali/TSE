# Data availability, gaps and enrichment gates

Date: 2026-11-11. Scope: current 794-workbook archive. See [inventory](dataset-inventory.md) and [official-source observations](iran-market-structure.md). “Supported” means a defensible calculation is possible from checked fields, not that a trading edge is demonstrated.

| Data capability | Current evidence | Analyses enabled | Missing evidence / next source | Gate |
|---|---|---|---|---|
| Four investor-category value amounts | Daily tables, header mappings and row/footer checks | Ownership net, value shares/intensity, concentration, rankings | Preserve exact amounts plus independent validity per field/row | Ready for descriptive milestone |
| Four investor-category volume amounts | Daily tables; independent volume checks | Quantity transfers, category execution VWAP when paired with valid value | Match symbol/session/scope and preserve instrument-unit semantics | Ready conditionally |
| Historical observations | 769 market-total dates, 790 symbol-analysis dates; changing symbol coverage | Observed-window persistence and descriptive activity/flow baselines | Session calendar and missingness reasons; stable instrument master | Supported with explicit coverage; no prediction claims |
| Summary and investor footer totals | Summaries sometimes disagree with reconciled details | Reconciliation, source-quality alerts, independent detail/summary reporting | Keep report-family scope and exact mismatch values | Reuse current selective validation |
| Percentages and top-three panels | Narrower shares/rights scope and 0–100 vs 0–1 scales | Source-scoped cross-checks | Explicit denominator population and scale | Do not mix into full-universe aggregates |
| Immutable identity/classification | Raw symbols/names; no dated master | Exact-label analysis only | TSETMC instrument master: insCode, instrumentID, cIsin, type, venue/board/industry plus valid-time mapping | No suffix stripping or equity-only labels before verified mapping |
| Dated sector membership | Absent from daily contract | Sector flows, rotation, relative comparisons | Dated instrument/industry classifications and corporate-change history | Backlog; current classifications do not establish past membership |
| Official OHLC, close, last and trade value/count | Not in daily ownership tables; official endpoints observed during research | Returns, RSI/MACD/ATR, realized risk, turnover relative to price history | Versioned daily TSETMC price history, synchronization/finality, venue/source scopes | Enrichment milestone; current category VWAP is not a substitute |
| Corporate actions and total return | None in current daily contract; adjustment-list fields observed | Comparable returns, value/momentum factors, portfolios | TSETMC adjustment records + CODAL event/cash-flow details; ex-dates, effective times and adjustment policy | Block return claims until policy reconciles raw prices and cash flows |
| Client-category counts | Absent in Excel; current endpoint observed, dated history/semantics unresolved | Source-reported average value per count and buy/sell “power” heuristics | Authoritative definition of account/person/code/execution count and historical endpoint coverage | Block per-investor labels; current counts cannot backfill historical behavior |
| Capitalization, free float and outstanding units | Absent from daily tables | True share turnover, capacity, size/valuation factors | Dated capital/share/unit master and free-float records | Value/volume alone cannot infer tradable float or market cap |
| Quotes/order books/executions | Absent; current market-watch levels observed | Spread, depth, order-book imbalance, queue/limit-state analysis | Timed archival book/print data with side, unit and correction definitions | No queue duration, aggressive flow, spoofing or guaranteed-fill claims now |
| Halt/phase/limit/base-volume history | Not longitudinal; one market-review sheet has supervisor notices | Executable backtests, censoring-aware return analysis | Dated TSETMC states/thresholds + TSE/IFB/SEO rules and supervisor notices | Resolve false-success/default state responses; do not impose today's rules historically |
| Financial statements/disclosures | No supported financial contract; CODAL search metadata observed | P/E, book-to-market, profitability, accruals, event studies | Original CODAL statement versions, publication timestamps, accounting units, restatements and issuer links | Reporting period end is not availability; current corrected statements are not historical vintages |
| Market/sector/total-return benchmarks | Sparse one-date/period index sheets only | Excess returns and factor evaluation | Dated index histories with price vs total-return definitions and investability | No synthetic benchmark from investor VWAP |
| Inflation, FX and risk-free reference | Absent | Real activity, macro exposures, nominal-vs-real risk/valuation | Official CBI/SCI series, release vintages; explicitly named FX market and units; investable dated bill/fund benchmark | No spliced official/free-market FX or revised macro hindsight |
| Fees, taxes, spread, settlement and borrowing | No executable schedule stored | Net strategy returns and portfolio cash accounting | Dated SEO/venue/clearing schedules with type/board scope; official fee bulletin examined as informational evidence | No universal constant fee, T+N, short-sale or same-day-reuse assumption |
| Publication/first-observed/correction ledger | Source publication strings and attachment IDs; offset not verified; indexed_at is later processing time | Provenance, but not certified historical availability | Append-only attachment observations, fetch timestamps, timezone confidence, publication/amendment events, as-of resolver | Required before forward-return tests; unknown-time data stay descriptive |

## Minimum provenance contract

Retain immutable original bytes, SHA-256, attachment/report IDs, source URL/name, download-observation time, raw publication/effective strings, parsed calendars, timezone confidence, parse/version timestamps and every source correction. At row level retain sheet, Excel row/cell and original heading; store exact numeric text, parsed Decimal, unit, scale, validity and reason. At metric level retain formula version, source observation IDs, eligibility mask, universe definition, denominator, exclusions, temporal cutoff and parameters.

A source revision's public timestamp, the collector's first observation and the parser's indexing time are distinct. A retrospective archive cannot recreate unobserved past versions simply by assigning today's file to an old trading date.

## Enrichment order and stop conditions

1. **Identity and calendar pilot:** resolve a small, diverse sample (ordinary share, right, fund, block/special channel, delisted/renamed label). Validate time ranges and retain ambiguous mappings unresolved. No bulk merge based only on normalized text.
2. **Daily prices and actions pilot:** verify units, official close versus last, value/quantity consistency, adjusted/unadjusted history, dividends/capital changes and missing/zero-trade sessions. Halt on conflicting types, unexplained adjustments or stale endpoint responses.
3. **Availability ledger:** verify publication timezone and append-only version records before any historical signal/return join. If only “latest corrected history” is available, label the study retrospective and quantify unavailable-vintage limitations; do not market it as point-in-time.
4. **Execution pilot:** obtain scoped dated rules, costs and state/limit data. Without queue evidence, a limit-locked signal has an unverified fill; order simulations must use explicit conservative no-fill/partial-fill rules and sensitivity bounds.
5. **Fundamental/macro enrichment:** add original release versions after identities and timestamp discipline exist. Validate units, consolidation scope, fiscal calendars and restatements independently.

Use cached, throttled, retrying read-only adapters; respect source service terms and rate limits. A successful request is not evidence of licensed redistribution, a guaranteed public API contract, or full archival history. Raw enrichment snapshots belong in ignored storage, not Git.

## Important semantic exclusions

- Individual net buying is ownership transfer between categories, not fresh aggregate money entering an exchange.
- Category counts do not establish beneficial-owner identity or motives. A fund's institutional counterparty may be a market maker.
- Executed value/quantity is not order-book aggressor imbalance. Daily investor categories do not encode buyer/seller initiation.
- A mixed-instrument aggregate of rial trading value is meaningful only with a stated population; summed quantities across different contract units need stronger classification.
- Missing rows are unknown, not zero activity. Non-trading, halted, delisted, unavailable-source and invalid-row states need separate reasons.
- A popular tablokhani heuristic can be implemented as an explicitly named descriptive statistic without inheriting its claimed predictive interpretation.
