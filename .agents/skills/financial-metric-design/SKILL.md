---
name: financial-metric-design
description: Use when defining or reviewing financial indicators, denominators, aggregate metrics, or calculation edge cases for Iranian market data.
---

# Financial metric design

A metric is a mathematical contract before it is a financial interpretation. Use this reference with Superpowers TDD; it does not replace that workflow.

## Required design record

Record name, purpose, evidence class, exact equation, input fields and units, population, availability cutoff, denominator, eligibility mask, missingness behavior, reconciliation tolerance, expected range, output precision, version, sources and validation plan.

| Question | Required distinction |
|---|---|
| What is measured? | Execution value, quantity, price and participant count have different dimensions. |
| Across whom? | Investor categories, individual investors and instruments are different populations. |
| Which denominator? | Total one-sided turnover, category activity and gross absolute transfer answer different questions. |
| How certain? | Accounting identity, descriptive construction and predictive hypothesis require different evidence. |

## Research and calculation steps

1. Retrieve the original definition or authoritative mathematical documentation. Record access level; a library establishes semantics, not investment usefulness.
2. Derive units, bounds and invariants. Define aggregation weights and duplicated information.
3. Reconcile exact source amounts with Decimal. Preserve residuals; tolerated imbalance does not establish exact conservation. Do not clamp invalid ratios into bounds.
4. Specify unavailable outputs for zero denominators, missing fields and invalid scope. Distinguish explicit zero from missing.
5. Prepare independent hand calculations and tests for scale invariance, category swaps, row permutations, partial coverage, ties and degenerate cases.
6. Define usefulness separately: reliable description now; chronological, multiplicity-aware validation before predictive claims.

## Example

For values in rial, RB=60, IB=40, RS=30, IS=70: T=100; retail transfer N=30; intensity N/T=.30. Retail activity imbalance N/(RB+RS)=1/3 is different. Institutional transfer is -30 only under exact conservation.

For instruments with turnover 100 and 300, instrument-turnover HHI=(.25)^2+(.75)^2=.625 and effective instrument count=1.6. Squaring retail/institutional shares measures category concentration instead. Neither reveals individual-investor concentration.

## Eligibility example policies

Use buy-side T=RB+IB and residual R=T-(RS+IS). A checked row within the existing 1-rial tolerance retains raw transfer and residual; normalized intensity additionally needs T>0 and |N|<=T. Otherwise it is null with a reason. Institutional net is computed independently. Complete-market outputs require complete checked tables; partial outputs describe only named eligible instruments with observed/excluded counts, never full-market estimates.

If T>0,N=0, intensity is zero; if T=0, it is null. All-zero turnover makes HHI/effective count null; a zero-weight row in a positive-total population contributes zero. All-zero transfers make cancellation and nonzero-sign breadth null. A missing input remains missing.

## Sources and failures

Use project research source registers, DOJ HHI definitions (fractional versus percentage scaling), NIST robust statistics and original papers for proposed return relationships. Do not transfer antitrust thresholds to trading concentration. Never label transfer as cash newly entering an entire market, execution VWAP as official close, or association as alpha.

## Output

Produce the design record, hand fixture, failure/null cases, citations, implementation gate and required tests.
