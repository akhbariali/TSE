# Feature prioritization and incremental roadmap

**Proposal, awaiting approval.** These scores rank engineering value and feasibility; they are not estimates of expected returns or predictive confidence. Method/source detail belongs to the [catalog](analysis-catalog.md), [methods evidence](methods-evidence.md) and [gaps](data-gap-analysis.md).

## Scoring method

Eight dimensions use 0–3, higher is more favorable: D=data availability (none/partial/pilot/checked now); I=Iran relevance; X=interpretability; R=calculation robustness; E=evidence for the **stated descriptive or predictive purpose**; F=implementation feasibility (high effort=0, low effort=3); V=ability to evaluate usefulness with current data; S=safety from misleading interpretation (higher is less risk). Equal-weight total out of 24 is transparent triage, not a scientifically estimated utility function. Scores are researcher judgments, not empirical measurements; no decimal precision or implied statistical certainty.

**Hard gates override totals:** identity/type gaps block equity/sector labels; missing prices/actions block return calculations; unknown availability blocks strict predictive evaluation; missing execution/rule history blocks implementable strategy claims. A high score cannot authorize a missing-data feature.

| Candidate / stated purpose | D | I | X | R | E | F | V | S | Total | Gate / phase |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Reconciliation, missingness and coverage diagnostics |3|3|3|3|3|3|3|3|24| Mandatory foundation, M1 |
| Ownership transfer and intensity, descriptive |3|3|3|3|3|3|3|2|23| M1; bounds/residual checks |
| Flow-sign breadth, descriptive |3|3|3|3|2|3|3|2|22| M1; explicit denominator |
| Trading-value HHI, effective count, top-k |3|3|3|3|3|3|3|2|23| M1; instrument rather than investor concentration |
| Counterflow cancellation, descriptive custom construction |3|2|3|3|1|3|3|2|20| M1; no alpha claim |
| Reproducible report and web snapshot views |3|3|3|3|3|2|3|3|23| M1; same verified artifact in CLI/UI |
| Category execution VWAP comparison |2|3|2|2|3|2|2|1|17| M2 candidate; matching value/quantity scope |
| Cumulative observed transfer |3|3|3|2|2|3|2|1|19| M2; no inferred holdings |
| Matched-panel change decomposition |2|3|2|3|3|2|3|3|21| M2; exact-label comparisons only until identity |
| Trailing MAD activity/flow anomalies |2|3|3|2|3|2|2|2|19| M2; minimum history, no zero-MAD score |
| Streaks, transitions, flow persistence |2|3|3|2|2|2|2|1|17| M2; session/gap checks, simple baselines |
| Entropy / distribution shifts |2|2|2|2|3|2|2|2|17| M2 research; overlap with HHI, added value required |
| Identity, calendar and availability ledger |1|3|3|3|3|1|2|3|19| M3 foundation pilot |
| Sector flows and rotation |0|3|3|2|2|1|1|2|14| M3; dated classification required |
| True share/free-float turnover |0|3|3|3|3|2|1|2|17| M3; dated denominator required |
| Price momentum / volatility / drawdown |0|3|3|3|3|2|1|2|17| M3; adjusted prices/actions required |
| Amihud illiquidity proxy |0|3|2|2|3|2|1|1|14| M3; returns/value, limits/zero-trades |
| Buyer/seller per-count power heuristic |0|3|2|2|1|2|0|0|10| M3 research; count definitions/history required |
| Flow factor return hypothesis |0|3|2|2|1|1|0|0|9| M4; PIT prices/universe/validation |
| Fundamental value/profitability/accrual factors |0|3|2|2|3|0|0|1|11| M4; original CODAL vintages |
| Order-book imbalance, queue and impact measures |0|3|2|1|3|0|0|0|9| M4; historical book/executions required |
| Shrinkage risk model / constrained allocation |0|3|2|2|3|1|0|1|12| M4; return panel, exposures, constraints |
| Macro-conditioned signals |0|3|1|1|1|0|0|0|6| Later exploratory; release vintages and regime risk |
| Flow clusters, network/change-point models |1|2|1|1|1|1|1|0|8| Later exploratory; do not infer hidden owners or causality |
| Execution-aware strategy backtesting |0|3|2|1|3|0|0|0|9| M4 gated infrastructure, no assumed fills |

## Roadmap and measurable gates

**M1 — Ownership research snapshot, artifacts and webapp views.** Four metric families, exact parser adapter, reproducible JSON/CSV/Markdown and provenance manifest. Add an existing-app Research snapshot view and report-library entry points; use server artifacts for all calculations. The sample provides independent accounting anchors. Accept only after unit/invariance tests, source reconciliation, deterministic repeated output, safe partial-data behavior and independent review. No new runtime dependencies or schema migration. [Detailed plan](../superpowers/plans/2026-11-11-ownership-research-snapshot.md).

**M2 — Historical descriptive research.** Test whether flows/activity differ from the same label's past compatible observations; add matched-panel changes, trailing-only MAD and one persistence baseline. Declare calendar gaps and exact-label identity limitations. Compare alerts with source errors and universe changes, not investment returns. Promote additional entropy/VWAP features only if they convey information beyond M1 and pass scope checks.

**M3 — Small enrichment/provenance pilot.** Dated security identities/classifications, session calendar, append-only publication observations, price/action consistency, selected benchmarks. Cover a share, right, fund, special channel and renamed/delisted observation. Demonstrate both positive joins and safely unresolved cases. Current endpoint snapshots cannot reconstruct historical states. Resolve timezone/finality before predictive data joins.

**M4 — One preregistered investment hypothesis.** Test one flow hypothesis against momentum/size/liquidity baselines with nested chronological selection and untouched evaluation. Require corporate-action-aware outcomes, survivorship handling, exposure/capacity accounting and dated cost/halt/limit/queue rules. Report no-fill and adverse-cost scenarios. Negative/null results remain valid outcomes; add methods only after evaluating incremental value and recording every trial.

## Deliberately deferred

A large indicator library, opaque smart-money score, automatic institutional-following advice, investor-level herding from two categories, simulated guaranteed queue fills and LLM-generated financial values are not justified by current evidence. Future methods remain catalog entries with explicit missing-data gates rather than half-working production features.
