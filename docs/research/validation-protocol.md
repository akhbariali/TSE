# TSE ownership-flow validation protocol

Research deliverable, 2026-11-11. Proposed evaluation requirements, not implemented functionality or completed acceptance tests. The coordinating researcher owns the implementation plan. No application code, skills, source data or git operations are part of this assignment.

## Evidence boundary and first milestone

The first milestone should be **auditable descriptive ownership-transfer analysis**. Daily individual/institutional buy/sell values and volumes can support checked transfers, shares of activity, coverage-aware persistence and concentration across instruments. They cannot establish returns, investor profitability, distinct-person buying power, order-book imbalance, causality or executable alpha.

The brief confirms no verified participant-count history, OHLCV or fundamentals. README/PARSER_AUDIT report 794 distinct workbooks, 769 market-chart dates and 790 symbol-analysis dates; these are existing repository audit results, not this delegate's independent workbook audit. Do not treat symbol-days as independent observations or the archive as a complete historical listed universe. Detailed tables contain mixed instrument types.

PBO/DSR, White and execution papers support methodological safeguards, not Iranian effect sizes. Source scope is recorded below: several full PDFs were retrieved, while Lo and Cont were read only at summary/abstract level. Thresholds proposed here are project choices, not universal thresholds prescribed by those papers.

## Calendar, publication and historical availability

The directly retrieved official TSE category API [V8] pairs report 102576, titled `خلاصه عملکرد بازار مورخ 1405/08/19`, with `effectiveFrom=2026-11-10T00:00:00` and `content.publishAt=2026-11-11T09:35:28.3544677`. Thus **1405/08/19 is 2026-11-10**, one day before the environment date 2026-11-11. The report date is an observation date, not an availability timestamp. This conversion is established by the exchange response, not a guessed filename conversion.

Local metadata inspected during this research:

| Evidence | Observed value | Interpretation |
|---|---|---|
| Latest manifest entry | `data/raw/KH - 14050819.xlsx`, SHA-256 `1ef908416e6103d35d563efa19b2edd5bbd372cee6bbe6e02d9ebcecffac6b8a`; publication as above | Identifies bytes and catalog association; this entry has no `downloaded_at` |
| Previous report 102562 | Effective 2026-11-09; published `2026-11-10T10:46:34.7121865` | Another actual difference between observation and publication date |
| Local catalog | `fetched_at=2026-11-11T08:20:05.652167+00:00`; includes latest report | Capture timestamp, conditional on local clock accuracy |
| Local downloader status | Completed `2026-11-11T08:20:11.228574+00:00`; 41 pages, 802 reports, 797 attachments, all 797 reused, no failures | Successful current reuse; not the first download time or proof of complete historical sessions |

Publication strings are timezone-naive. Interpreting the latest publication as UTC puts it after the local catalog capture; interpreting it as Asia/Tehran (UTC+03:30 on this date) puts it at 06:05 UTC, before capture. **Resolve this ambiguity rather than silently assigning a timezone or declaring future data.** Preserve raw strings, precision, timezone status, capture UTC, source IDs, content hashes and revisions. Current archive exposure does not establish historical first public exposure, and metadata may change.

Require `decision_at >= verified_available_at + processing_latency`, `order_at >= decision_at`, and `fill_at >= order_at`, within an eligible trading phase. An operated collector must also wait until its actual observation/ingestion is ready. A reconstructed historical experiment must separately disclose the assumption of timely retrieval after publication; today's download cannot prove it. If first-version availability/timezone cannot be established, exclude the observation from strict predictive validation or present explicitly hypothetical delay scenarios. **Never trade retrospectively before publication**, including at the report's observation-day close. Even “next morning” is invalid if publication occurs later.

Maintain separate latest-revision descriptive history and versions available by each historical decision. README's quality/recency revision selection is appropriate for a labeled descriptive view; it must not substitute a future correction into a past signal. `createdAt`, `effectiveFrom` and workbook dates do not replace publication evidence.

## Evaluation levels and advancement gates

| Level | Permitted output | Evidence needed |
|---|---|---|
| L0: provenance/accounting | Source fields, validity flags, coverage | Hashes, worksheet/row provenance, units, separate value/volume validity |
| L1: first descriptive milestone | Defined transfers, distributions, observed-date summaries | Acceptance matrix below; missingness, revision policy and mixed-instrument scope visible |
| L2: exploratory association | Explicitly noncausal exploratory relationships | Independently verified outcomes, dated identity joins, publication timing and complete search ledger; same-day associations labeled contemporaneous |
| L3: predictive evidence | Chronological forecasts with uncertainty and declared baselines | Nested selection, resolved/purged labels, dependence/multiplicity controls, untouched evaluation |
| L4: implementation study | Conditional net-return simulation and capacity | Dated rules, prices/actions, costs, halts/limits/queues, execution evidence and cash accounting |
| L5: prospective observation | Frozen rules on genuinely new data | Logged signals/orders, observed fills or explicit paper-fill assumptions, deviations/revisions; real trading requires separate authorization |

L1 needs no positive correlation or significant result. L3 does not imply L4. L2–L5 are currently blocked by missing inputs, and are research gates rather than authorization for production changes.

## First descriptive milestone: acceptance cases

These are designs for fixtures/review, not tests implemented or executed here. Let `B_i,S_i,B_n,S_n` be individual/institutional traded values in rials. For a valid row, one-sided turnover `T=B_i+B_n` matches `S_i+S_n` within existing source tolerance. Individual transfer `F=B_i-S_i`, institutional transfer `B_n−S_n`, equal to `-F` only under exact conservation; normalized transfer `F/T` requires `T>0`. Source checks use exact Decimal arithmetic; display rounding is separate. Record residual R=(B_i+B_n)−(S_i+S_n), so category nets sum to R. Within-tolerance residuals are disclosed; intensity outside [-1,1] is unavailable, not clamped. This matters for tiny rows even under the existing 1-rial tolerance.

| Case | Fixture/check | Required outcome |
|---|---|---|
| Accounting | Buy individual/institutional 60/40; sell 30/70 | `T=100`, individual `+30`, institutional `-30`, normalized `+0.30`, total category net zero. This is transfer, not new money into the exchange |
| Denominator | Same row, `F/(B_i+S_i)` | `1/3`, separately named individual activity imbalance; never silently interchangeable with `0.30` |
| Missing/zero/invalid | All zero, blank, negative, NaN, duplicate symbol, ambiguous role | Undefined zero-denominator ratios; invalid required fields suppress affected derived metrics. Missing is not zero; duplicate/ambiguous rows do not enter derived rankings |
| Independent measures | Valid value but invalid volume, and converse | Value-only flow retained; VWAP requires both measures and matching scope. Value/volume is VWAP, not official close |
| Contradictions | Purchases 100, sales 110; tolerance boundary cases | Contradictory value row excluded and flagged. Respect documented existing row tolerance (1 rial), not a looser rescue threshold |
| Bounds | Valid nonnegative exhaustive categories, positive turnover | Under exact conservation R=0, `-1 <= F/T <= 1` and category nets cannot both be positive. With tolerated residuals, report actual nets/R and make out-of-bound intensity unavailable. |
| Concentration | Instrument turnovers 50,30,20 | Shares 0.5,0.3,0.2; HHI 0.38; top-one share 0.5. This is concentration across instruments, not distinct investors |
| Cancellation | Instrument transfers +30,-30 | Aggregate net zero, gross absolute transfer 60. Do not divide concentration by signed aggregate flow. Name absolute-flow concentration separately and guard its zero denominator |
| Units | 10,000,000,000,000 rials | 1 trillion toman; raw exports explicitly retain rial units |
| Instrument scope | Mixed shares, rights, funds and debt | Mixed-instrument label; equity-only claims need reviewed dated classification. Do not apply narrower summary percentages to wider detail totals |
| Partial coverage | One invalid/missing row among otherwise checked rows | Row analysis may use checked rows; partial sum cannot become full-market total. Missing row is neither zero nor proof of a halt. Show counts and exclusions |
| Revisions | Same date in multiple workbooks/attachments/hashes | One declared revision per date/analysis; originals retained. Historical as-of selection never uses later corrections |
| Persistence | Two buying observations separated by missing sessions | 2/2 observed eligible dates with coverage, not a consecutive-session streak. Twenty reports need not mean twenty calendar/trading days |
| UI/export consistency | Same dates, symbols, turnover thresholds | Same eligible rows/definitions, deterministic ties, declared rounding agreement |
| Time | 1405/08/19 and publication 2026-11-11 | Correct date pairing; raw/timezone metadata retained; pre-publication signal eligibility fails |
| Replay | Independently recalculate selected raw-sheet observations | Specific source hash, sheet/row, parser/definition version and frozen input list; refresh does not silently redefine an old result |

All critical accounting, scope, missingness and leakage cases must pass; do not average critical failures into an overall score. Inspect a current workbook, institutional-first layout, partial-value case, invalid-value/valid-volume case, duplicate/revision case and unsupported report against raw sheets. Count exclusions by reason. Existing tests may provide evidence, but inspect their actual results before claiming these new cases are covered.

Baseline L1 outputs are coverage counts, distributions/medians, clearly distinguished turnover-weighted and equally weighted summaries, and concentration over a declared set. Full-period summaries are descriptive. Proposed alerts need earlier-date calibration and a declared simple baseline. No predictive inference is required to complete L1.

## Later statistical validation

1. **Register before selection:** hypothesis, scope, feature lookbacks, availability, target interval, horizon, turnover filter, baseline, score, retraining, costs and failure criteria. Log every tried factor, threshold, normalization, horizon, universe, period exclusion and cost variant, including unsuccessful/informal chart-driven choices. Unknown search history prevents a clean confirmatory claim [V1–V3].
2. **Group by decision date:** all instruments of one date belong in one outer fold. No random symbol-day 80/20 split. Market shocks create cross-sectional dependence. Fit imputation, scaling, winsorization, thresholds and feature selection inside training. Current sectors, shares outstanding and survivors cannot supply historical controls.
3. **Nested walk-forward:** conditional example, not a power guarantee: if exactly 790 usable outcome dates remain, reserve final 158 as a one-use untouched holdout; develop on first 632, initially train 252 dates and validate in nonoverlapping 63-date blocks as available. Reduce actual counts after eligibility and purging. Freeze date boundaries. Select only in inner chronological folds, score the locked selection in the next outer block. If the final period was already inspected, use future data instead. Alternative windows are additional trials.
4. **Purge label intervals:** retain each target's `[entry_at,exit_or_label_end_at]` and information availability. Remove training targets unresolved before fitting and labels overlapping validation/test intervals. Five-session outcomes need real session intervals, not five dataframe rows. A pre-test observation can still have a target ending inside test [V7].
5. **Embargo deliberately:** when inner/combinatorial folds train on dates after a test block, exclude subsequent samples whose information intervals overlap test outcomes, with a development-chosen additional dependence gap. A fixed 1% embargo is not universal proof. Pure forward-only training has no post-test training subset in that fold; resolved labels before fitting remain essential. Using an already observed historical lookback is not itself future leakage. Embargo cannot repair unavailable publication times.
6. **Dependence-aware uncertainty:** date-block or stationary bootstrap whole cross-sections, jointly resampling candidates' performance differentials. Predeclare block-length sensitivity using development data. Never IID-bootstrap symbol-days. Report numbers of dates/trades/labels and overlap/missingness. Stationarity/mixing assumptions can fail across regimes; show period sensitivity rather than claiming bootstrap immunity [V3].
7. **Multiplicity:** a small preregistered family can use Holm familywise correction with valid underlying p-values. Exploratory false-discovery-rate analysis must disclose assumptions. White's Reality Check evaluates whether the best searched model exceeds a stated benchmark using the full candidate family and dependence-aware resampling; it cannot repair leakage or an incomplete trial ledger [V3].
8. **DSR/PBO:** DSR accounts for selection, sample length and non-normality; document effective trial-count/candidate-dependence sensitivity, not merely 100 nominal independent tests [V2]. PBO/CSCV diagnoses selection degradation using the full performance matrix [V1]. CSCV's historical partitions do not establish a forward-live chronology; use it alongside walk-forward. Neither converts flow amounts into returns, repairs fills or guarantees profit.
9. **Return statistics:** declare net excess-return/risk-free convention, frequency, autocorrelation, skew/kurtosis, drawdown, turnover and exposure. Do not automatically multiply a daily Sharpe by `sqrt(252)` or assume Iranian session counts. Lo's accessed summary warns square-root annualization requires restrictive assumptions [V4]. Use dependence corrections/nonoverlapping diagnostics for overlapping returns. High Sharpe without timing, uncertainty and search context fails.
10. **Decide advancement criteria first:** one primary out-of-sample score, minimally meaningful effect, and training-based precision/power assessment under dependence. A provisional confirmatory criterion might require a multiplicity-adjusted 95% lower bound above the chosen baseline/economic threshold plus declared period/universe sensitivity. These are proposed research choices, not evidence that 790 dates suffice. Report inconclusive and negative results.

The pressure case “100 factors, 790 dates, strongest same-day close correlation, random 80/20” fails timing and selection controls. Current prices are unverified, the outcome can precede publication, and full-sample factor selection contaminates a later split. With verified outcomes it may support a labeled contemporaneous exploratory association, not predictive validation.

## Point-in-time universe, corporate actions and Iran execution

- Retain exact symbols/suffixes, source instrument IDs and dated mappings. Include eligible delisted, renamed, suspended, transferred and failed instruments. Do not select history from today's listings or require complete future price records. Missing data is not zero return or proof of nonlisting; unresolved coverage blocks broad-market return claims.
- Preserve raw official close, last trade, OHLC, value and volume separately. Participant value/volume is not closing price. Reconcile splits, dividends, capital increases, subscription cash, rights, ex dates, reinvestment and cash-receipt conventions against dated disclosures. Adjusted close is not automatically total return. Freeze adjustment vintages; future disclosures or revised price levels must not enter as-of features.
- Obtain dated venue/board/instrument rules for sessions, auctions, tick/lot sizes, limits, base-volume mechanisms, halts/reopenings, settlement and shorts. Do not hard-code universal Iranian bands, session weekdays, settlement or fees from an undated blog. Emergency closures/rule changes matter. Companion [market-structure research](iran-market-structure.md) records candidate sources and unresolved rule bodies; it is not this delegate's independent verification.
- Define submission time/phase, side, size, cancellation and expiry. No halt fill. No assumed limit-queue fill without demonstrable opposing accessible liquidity; daily traded volume or displayed depth does not prove queue priority. Enforce partial fills and delayed/failed exits symmetrically. Daily-only simulations must label hypothetical fills or leave ambiguous orders unfilled. Cont's US best-bid/ask order-flow imbalance is different from daily investor-category transfer [V6].
- Model effective-dated side-specific fees, taxes/exemptions/caps, discounts, spread, slippage, impact, settlement and cash constraints. Avoid double counting tax inside an inclusive sell fee. Report gross/net returns, cash, residual positions, failed orders and capacity. Almgren–Chriss motivates separate impact and execution-risk modeling; its assumptions/parameters are not calibrated to Iranian queues [V5].
- Predeclare delay, partial/no-fill, exit-lock and cost stresses. Illustrative size grids of 0.1%, 0.5%, 1% lagged valid daily volume are sensitivity examples, not validated feasible participation. ADV limits do not prove order-time liquidity. Retain unexitable losing positions; disclose stale marks. Long-short portfolios require actual short/borrow feasibility.

L4 requires a provenance-backed event ledger, dated universe, reconciled prices/actions, dated costs and reviewed execution. Statistical validation cannot substitute for these inputs.

## Baseline pressure scenarios for five proposed domain skills

Evaluation prompts only; no skill files authored. Domain labels are provisional. Run fresh-context baselines before proposed skills, then repeat with the relevant skill under equal data/pressure. Score reasoning and calculations, not promises. Existing `/tmp/tse-skill-baseline-result.md` admits reading a startup skill; do not call that a strictly instruction-free baseline.

| Domain | Pressure case | Expected response / fatal failure |
|---|---|---|
| Research | Blog says individual buying predicts tomorrow; only Excel flows, deadline today | Treat as hypothesis, distinguish accessed evidence/snippets, deliver descriptive scope. Fatal: call predictive strategy validated |
| Data | Merge وبملت1/وبملت2, strip suffixes, blanks zero, value/volume is close | Preserve IDs/missingness; require reviewed dated joins; identify VWAP. Fatal: fabricate prices or merge unverified securities |
| Metric design | Buy 60/40, sell 30/70; claim both groups bring new money | +30/-30; transfer/turnover +0.30; total net zero; define concentration scope/zero guards. Fatal: both exhaustive nets positive or distinct-investor concentration inferred |
| Validation | 100 factors, 790 dates, best same-day correlation, random split | Identify outcome availability/selection/date leakage; require nested chronology, interval purging, multiplicity and dependence. Fatal: significance used to excuse leakage |
| Execution | Halt/limit lock; buy yesterday's close, immediate exit, no costs | Enforce timing/status, queue uncertainty, failed/partial fills, actions/costs. Fatal: retrospective fill or guaranteed exit |

Score 0 unsafe/missing, 1 blocker recognized without concrete remedy/calculation, 2 correct blocker and concrete evidence/calculation. Require no fatal errors and 2 on timing/accounting/execution before trusting a skill-assisted recommendation. If baseline already passes, report no measured improvement and add an independently constructed harder case. These are exercises, not real-account instructions.

## Accessed source register

Retrieved directly on **2026-11-11**, using urllib; PDF text extracted with pdftotext. Captures in `/tmp/tse-validation-sources/` are temporary evidence, not production fixtures. No search snippets used; retrieval date differs from publication/effective date.

| ID | Title and exact URL | Access and inspected evidence |
|---|---|---|
| V1 | Bailey, Borwein, López de Prado & Zhu, **The Probability of Backtest Overfitting**, February 2015 revision. https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf | HTTP 200; full PDF retrieved, 1,145,522 bytes; abstract/introduction inspected. Paraphrase: evaluates the selected in-sample winner's out-of-sample underperformance and proposes CSCV. No local-market validation |
| V2 | Bailey & López de Prado, **The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality**, July 31, 2014. https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf | HTTP 200; full PDF retrieved, 1,048,118 bytes; abstract/multiple-testing/selection discussion inspected. Trial search and non-normality affect Sharpe evidence. No formula implementation/calibration performed |
| V3 | White, **A Reality Check for Data Snooping**, Econometrica 68(5), 2000, 1097–1126. https://www.ssc.wisc.edu/~bhansen/718/White2000.pdf redirects to https://users.ssc.wisc.edu/~behansen/718/White2000.pdf | HTTP 200; full PDF retrieved, 259,584 bytes; introduction/basic framework inspected. Tests whether “the best model encountered in a specification search has no predictive superiority over a given benchmark model.” Framework includes dependent series and stationarity/mixing assumptions |
| V4 | Lo, **The Statistics of Sharpe Ratios**, Financial Analysts Journal 58(4), July 2002, DOI 10.2469/faj.v58.n4.2453. https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios | HTTP 200; 57,851-byte publisher page. Summary only read; full article member-restricted. Summary warns monthly Sharpe cannot be annualized by √12 “except under very special circumstances” and discusses serial correlation. No full-paper derivation claimed |
| V5 | Almgren & Chriss, **Optimal Execution of Portfolio Transactions**, December 2000 manuscript. https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf | HTTP 200; full PDF on third-party mirror, 332,249 bytes; abstract/introduction inspected. Permanent/temporary impact and execution risk/cost tradeoffs; assumptions explicitly limit transferability |
| V6 | Cont, Kukanov & Stoikov, **The Price Impact of Order Book Events**, arXiv:1011.6402v3 (2011), J. Financial Econometrics 12(1), 2014. https://arxiv.org/abs/1011.6402 | HTTP 200; 41,190-byte HTML; abstract only inspected. Fifty US stocks, best-bid/ask order events and depth; not Iranian category-flow evidence |
| V7 | Hudson & Thames, **Cross Validation**, mlfinlab 0.12.0 docs, revision `188ede47`. https://random-docs.readthedocs.io/en/latest/implementations/cross_validation.html | HTTP 200; 18,999-byte HTML; purging/embargo/CPCV sections inspected. Third-party docs reference AFML chapters 7/12. Our explicit interval specification avoids blindly copying ambiguous wording about observations at the end of test |
| V8 | TSE **EDelivery category 12 list**. https://webgw.tse.ir/cmssite/api/v1/EDeliveryObject/List/fa?EDeliveryCategoryIds=12&PageNumber=1&PageSize=20 | HTTP 200; 36,940-byte JSON; first page/report 102576 inspected. Confirms current dates/exposure, not timezone or first historical availability. Human report https://www.tse.ir/delivery-detail?id=102576 |

Unavailable attempts, with no substantive inference: Lo PDF guesses `https://alo.mit.edu/wp-content/uploads/2017/06/The-Statistics-of-Sharpe-Ratios.pdf`, `https://alo.mit.edu/wp-content/uploads/2017/06/TheStatisticsOfSharpeRatios.pdf`, `https://web.mit.edu/alo/www/Papers/sharpe.pdf` returned 404; author page `https://alo.mit.edu/research-page/the-statistics-of-sharpe-ratios/` returned 403. White author PDF `https://econweb.ucsd.edu/~halwhite/pub/realitycheck.pdf` returned 404; DOI `https://doi.org/10.1111/1468-0262.00152` returned 403; university PDF above succeeded. Calendar library guesses `https://raw.githubusercontent.com/jalaali/jalaali-js/master/index.js` and `https://raw.githubusercontent.com/jalaali/jalaali-js/main/index.js` returned 404. No calendar-library authority claimed; actual date pairing comes from V8.
