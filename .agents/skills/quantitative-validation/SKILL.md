---
name: quantitative-validation
description: Use when testing financial hypotheses, selecting signals, comparing models, interpreting statistical significance, or evaluating historical research results.
---

# Quantitative validation

Use this domain reference with the generic verification/TDD skills. Correct arithmetic, association, prediction and executable investment performance are separate claims.

## Research sequence

1. Define the estimand, target horizon, eligible universe, information clock, simple baseline and smallest useful effect before selecting features.
2. Read original methods and record their assumptions. Sources: Bailey et al. PBO, Bailey/Lopez de Prado deflated Sharpe, White Reality Check, Lo Sharpe statistics; use project validation-protocol source register for exact URLs/access levels. These do not prove an Iranian premium.
3. Join point-in-time instrument identity, disclosures, report versions and outcomes. Keep session, publication, first observation, decision, order and fill timestamps separate. Unknown availability blocks strict predictive claims.
4. Split the entire panel by date; all instruments on a date belong to one fold. Fit normalization, feature selection and hyperparameters only inside training windows. Use rolling/expanding nested evaluation and an untouched later test.
5. Purge labels overlapping test intervals and choose an embargo based on label/information overlap. TimeSeriesSplit alone does not implement this. Missing sessions require a verified calendar.
6. Record every explored factor, universe, threshold and horizon. Choose multiplicity controls compatible with dependence and the selection process; BH on selected p-values does not repair repeated holdout peeking.
7. Use date/cluster-aware or block resampling for dependent data. Report effect sizes, uncertainty, stability, failures and baselines, not only p-values or the best Sharpe.

## Evaluation reference

| Claim | Evidence |
|---|---|
| Descriptive calculation | Independent hand fixture, units, invariants, source reconciliation |
| Flow forecasting | Later-date MAE/Brier/log loss versus lagged/median/unconditional baselines |
| Return association | Availability-aligned adjusted returns, rank IC and dependent-data uncertainty |
| Strategy | Net returns, drawdown, volatility, exposure, turnover, capacity, costs and no-fill sensitivity |

## Example

Selecting 100 factors on all 790 dates then declaring the last 20% a holdout is contaminated. Start a new genuinely untouched period or label results exploratory; historical re-splitting cannot undo knowledge already used. Same-day returns cannot be future outcomes of a report published the following morning.

## Common failures and output

Do not count symbol-days as independent dates, interpret failure to reject as proof, tune on the final test, use surviving end-date constituents, treat revised statements as original vintages or claim causality from correlations.

Produce a frozen experiment card, data/version manifest, temporal split diagram or ranges, search ledger, benchmark results with uncertainty, leakage audit, sensitivity results and a verdict limited to the supported claim level. Publish negative results too.
