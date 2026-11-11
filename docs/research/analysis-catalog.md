# Analytical opportunity catalog

**Draft for architecture and implementation-plan approval, 2026-11-11.** This is a researched opportunity set, not a claim that the methods have been implemented or predict Iranian returns. Start with a small descriptive snapshot; expand only after data and validation gates pass.

## Reading the catalog

Each candidate records its purpose, financial rationale, precise calculation, inputs and actual feasibility, enrichment sources, limitations, evaluation, effort and evidence. Complexity is relative engineering effort: **low** means pure formulas over checked existing rows; **medium** includes historical alignment or a new verified adapter; **high** includes point-in-time fundamentals, market-state execution or statistical research. It is not a delivery-time estimate.

Evidence classes: **Identity** = accounting/algebra; **Statistic** = established mathematical definition used descriptively; **Foreign empirical** = accessed evidence in another sample, not Iranian validation; **Heuristic** = proposed application or financial hypothesis without accessed local predictive evidence. A method may combine classes. A software implementation reference establishes feasibility, not profitability.

References **S1–S25** resolve to exact URLs and access scope in [methods evidence](methods-evidence.md#accessed-source-ledger); **M1–M16** to [official market-source observations](sources-market-structure.md#accessed-primary-sources); **V1–V8** to [validation sources](validation-protocol.md#accessed-source-register). These linked registers distinguish full papers, abstracts, documentation, metadata and access failures. **Arithmetic** denotes a definition stated here, not an unsupported claim that a cited paper studied this archive. No Iranian return effect has been estimated. Local literature discovery is incomplete; an Iran-related DOI discovered only as metadata is not empirical support.

### Shared data contract

For an instrument/session, let `RB,RS,IB,IS` be individual (حقیقی, retail label) and institutional (حقوقی) buy/sell **values in rial**; corresponding quantities are `qRB,qRS,qIB,qIS`. Define one-sided trading value `T=RB+IB`, net retail transfer `N=RB−RS`, institutional net `NI=IB−IS`, value residual `e=T−(RS+IS)=N+NI`, and `Q=qRB+qIB`. Buy plus sell totals double-count turnover. Quantities across unlike contract types are not automatically additive.

Use exact finite nonnegative Decimal inputs and independently checked measures, not approximate REAL serving columns. Current row acceptance includes a **1-rial tolerance**: this does not prove exact conservation, `NI=−N`, opposing signs or bounded intensity. Report actual residuals and counterpart values. For `I=N/T`, require `T>0` and `−1≤I≤1`; a tolerance-accepted row failing this bound has **unavailable bounded intensity**, with reason, and is never clamped. Preserve its independently valid source fields. No silent numerical repair.

**Now** means checked fields on eligible rows, not all 794 workbooks. The archive has 792 daily report-family workbooks; checked value rows occur on 790 distinct analysis dates, and 769 dates support complete market-table analysis. Partial rows support labeled symbol observations, not full-market sums. These are retrospective report views, not certified point-in-time datasets. See [inventory](dataset-inventory.md) and [gaps](data-gap-analysis.md). All “market” measures below mean the declared **reported-instrument population**, initially mixed and incompletely classified; they do not certify the entire Iranian equity market. Stable economic identities, sectors, participant counts, prices, fundamentals and execution histories remain enrichment gates.

## A. Market-wide analysis

### A1. Net transfer and pooled intensity — first milestone

- **Purpose/rationale:** distinguish the scale of category transfer from the amount of trading supporting it. A transfer records counterpart ownership exchange, not new aggregate cash entering the exchange.
- **Calculation:** `Nmarket=ΣN`; `Tmarket=ΣT`; pooled `I=ΣN/ΣT` when the denominator and bounds pass. Report `ΣNI` and `Σe` independently. An equal-weight mean of row intensities is a different statistic.
- **Inputs/availability/sources:** four checked value fields and complete compatible table; **now**. No external data for the descriptive result; classification is needed for equity-only scope.
- **Weaknesses/evaluation:** large mixed instruments dominate; nominal levels shift with inflation and universe coverage. Reconcile to eligible detail totals, disclose footer differences/residuals and compare matched populations. No return inference.
- **Complexity/evidence:** **low; Identity + descriptive ratio**. Arithmetic; inventory; S22 does not validate “retail uninformed/institution informed.”

### A2. Active-sign ownership breadth — first milestone

- **Purpose/rationale:** show whether positive transfer is broad or confined to a few reported instruments.
- **Calculation:** count `n+=#(N>0)`, `n−=#(N<0)`, `n0=#(N=0)`; **directional balance** `B=(n+−n−)/(n++n−)` if nonzero denominator. Publish zeros, missing and exclusions separately. The all-observation version `(n+−n−)/(n++n−+n0)` is a separate named measure, not interchangeable with B. Optional turnover-weighted sign balance is `ΣT sign(N)/ΣT`.
- **Inputs/availability/sources:** valid values and declared population; **now**. Dated classifications later.
- **Weaknesses/evaluation:** equal sign weighting overweights tiny instruments; weighted signs ignore transfer magnitude. Compare pooled intensity, counts, matched coverage and turnover strata. Not price advance/decline breadth.
- **Complexity/evidence:** **low; Statistic/Heuristic application**. Explicit sign arithmetic; methods #7–8.

### A3. Trading-value concentration, top-k and effective count — first milestone

- **Purpose/rationale:** assess dependence of the day's activity on dominant instruments.
- **Calculation:** for `ΣT>0`, `s_i=T_i/ΣT`, `HHI=Σs_i²`, `Neff=1/HHI`; top-k share sums the largest `min(k,n)` weights. Zero-total population returns unavailable. Ties use a deterministic source-label key.
- **Inputs/availability/sources:** complete checked value table; **now**. No new source; separate classes once identities are verified.
- **Weaknesses/evaluation:** concentration of traded value is neither investor ownership concentration nor risk diversification. No antitrust thresholds apply. Check equal weights (`HHI=1/n`), single instrument (`1`), scale invariance, dominant-instrument exclusions and duplicate protection.
- **Complexity/evidence:** **low; Statistic**. S1 establishes squared-share arithmetic; reciprocal count is its equal-share equivalence, not a count of people.

### A4. Matched-population and entry/exit decomposition

- **Purpose/rationale:** separate changed behavior from changed observed coverage.
- **Calculation:** for adjacent reports, `C=U_t∩U_(t−1)`; `ΔΣN=Σ_C(N_t−N_(t−1))+Σ_entrants N_t−Σ_exits N_(t−1)`. Report intersection size and value coverage; never interpret a missing row as zero trading.
- **Inputs/availability/sources:** dated checked rows; **now for exact-label report comparisons**. TSETMC dated identity/type mappings and exchange calendars are needed for economic continuity (M4, M12).
- **Weaknesses/evaluation:** an unchanged text can hide security changes; renamed securities look like entry/exit. A fixed cohort selected using surviving end-date names is biased. Test decomposition exactly and manually audit label transitions, gaps and coverage.
- **Complexity/evidence:** **medium; Identity + Heuristic application**. Algebra; methods #14; M4 identifies current mapping possibilities, not historical completeness.

## B. Investor behavior and capital flows

### B1. Category participation and activity imbalance

- **Purpose/rationale:** distinguish an investor category's share of trading from its net transfer.
- **Calculation:** retail buy share `RB/T`, sell share `RS/(RS+IS)`, and retail activity imbalance `(RB−RS)/(RB+RS)` when the stated denominator is positive. Buy/sell shares have separately reconciled denominators; intensity A1 is different.
- **Inputs/availability/sources:** checked values; **now**. No external source for descriptive arithmetic.
- **Weaknesses/evaluation:** a high buy share alone can coexist with equally high sell participation. Category aggregation hides account heterogeneity and market making. Verify bounds, denominators and conservation residuals; compare with net and gross category activity.
- **Complexity/evidence:** **low; Identity/Statistic**. Arithmetic; S22's US account findings do not establish motives or skill in these categories.

### B2. Cumulative transfer and institutional accumulation/distribution proxy

- **Purpose/rationale:** describe sustained executed category transfer, a defensible limited interpretation of accumulation/distribution.
- **Calculation:** `C_i(h)=Σ_window N_i`; normalized `C/Σ_window T`. Institutional transfer is independently summed from `NI`, with residual reconciliation. Window identifies actual sessions/observed dates and all gaps.
- **Inputs/availability/sources:** checked historical values; **now for observed-date sums**. Dated calendar/identities and availability ledger needed for session-contiguous or predictive claims.
- **Weaknesses/evaluation:** no initial inventory, full ownership register or outside-population transfers: C is not holdings or ownership percentage. Inflation and reporting gaps matter. Audit coverage and reset rules; compare prespecified windows and future flow behavior, not invented returns.
- **Complexity/evidence:** **medium; Identity + Heuristic interpretation**. Arithmetic; methods #4; M4 for future identity mapping.

### B3. Source-count average trade value and “buyer power” hypothesis

- **Purpose/rationale:** investigate popular سرانه خرید / قدرت خریدار claims only after count meanings are established.
- **Calculation:** if matched count definitions are verified, `aB=RB/cRB`, `aS=RS/cRS`, ratio `aB/aS`, all denominators positive. Name averages per source-defined count; unique-person language requires explicit proof.
- **Inputs/availability/sources:** category values plus historical dated matched counts; **blocked**. Excel trade counts are not participant counts. M7 live endpoint and M9 wrapper are discovery paths; historical route/semantics unresolved.
- **Weaknesses/evaluation:** account splitting, intraday round trips and large investors distort averages; this does not measure order size or informed buying automatically. Verify counts, dates, populations, source duplicates; evaluate incremental held-out association after liquidity/size controls.
- **Complexity/evidence:** **medium/high; Heuristic**. M7/M9 establish fields, not distinct-investor definitions or predictive validity.

### B4. Sign persistence and transition behavior

- **Purpose/rationale:** identify recurring transfer directions and distinguish them from an unconditional tendency to buy.
- **Calculation:** estimate `P(sign N_(t+1)=b | sign N_t=a)` on verified adjacent sessions; positive-run length ends on nonpositive value or unknown session. Observed-date positive fraction is separately `npositive/nvalid`.
- **Inputs/availability/sources:** historical valid rows; **conditional now** for observed-date behavior; calendar/identity/availability enrichment needed for adjacent-session forecasting.
- **Weaknesses/evaluation:** split execution, price constraints and reporting artifacts mimic persistence. Do not bridge gaps or assume 50% baseline. Compare chronological Brier/log-loss scores with trailing unconditional-frequency baselines and report sample counts.
- **Complexity/evidence:** **medium; Heuristic**. Probability arithmetic; methods #16; validation protocol governs predictive evidence.

## C. Individual stock/instrument analysis

### C1. Category execution VWAP and buy/sell premium

- **Purpose/rationale:** describe different execution-price mixes within an instrument/session.
- **Calculation:** `vRB=RB/qRB`, `vRS=RS/qRS`; premium `vRB/vRS−1`, where denominators are positive and units match. Report all category VWAPs, without treating their differences as profit.
- **Inputs/availability/sources:** independently checked value and quantity for identical scope; **conditional now**. Verified instrument units needed before share-price naming. M5 price enrichment enables separate official-close comparison.
- **Weaknesses/evaluation:** timing, trade mix, blocks and instrument multipliers explain differences. VWAP is not last price, official close, cost basis or realized return. Test units and weighted reconstruction; manually verify matched raw cells before ranking.
- **Complexity/evidence:** **low/medium; Identity**. Value/quantity arithmetic; M5 explicitly has distinct price fields.

### C2. Value-share versus quantity-share divergence

- **Purpose/rationale:** identify whether category activity has a different price mix from total executions.
- **Calculation:** buy divergence `d=RB/T−qRB/Q`; for positive category quantity, `d=(qRB/Q)[(RB/qRB)/(T/Q)−1]`. Analogous sell measure uses sell totals.
- **Inputs/availability/sources:** checked paired tables, equal population and verified units; **conditional now**. No extra source after unit reconciliation.
- **Weaknesses/evaluation:** largely a transformation of relative VWAP, not independent “smart money” evidence. Different volume/value table coverage invalidates it. Verify the algebra and compare rankings with C1 to quantify redundancy; inspect scale errors and extreme denominators.
- **Complexity/evidence:** **low/medium; Identity + Heuristic application**. Methods #6; arithmetic, with no accessed local predictive evidence.

### C3. Cross-sectional intensity ranks

- **Purpose/rationale:** rank comparable observations while displaying both magnitude and trading activity.
- **Calculation:** percentile rank of bounded `I_i` within an explicit eligible universe; define tie convention. Display N, T and exclusions alongside rank. A minimum-activity filter must be declared, not optimized on later outcomes.
- **Inputs/availability/sources:** checked values; **now as a mixed-instrument descriptor**. Dated common-equity classification and prices required for stock-factor returns.
- **Weaknesses/evaluation:** high ranks can reflect negligible T; cross-class comparison may be meaningless. Test ties, missingness, scale and universe sensitivity. Later compare rank IC/quantile outcomes against liquidity and momentum baselines using H1/H4.
- **Complexity/evidence:** **low now, high as strategy; Statistic + Heuristic**. Methods #20; no established Iranian flow factor claimed.

### C4. Price momentum

- **Purpose/rationale:** test international evidence of return continuation as a benchmark for proposed ownership signals.
- **Calculation:** example formation-month signal `M_t=Π_(j=2..12)(1+r_(t−j))−1`, explicitly skipping the most recent completed month; trading occurs only after the formation cutoff. Factor replication also needs dated size breakpoints.
- **Inputs/availability/sources:** adjusted/total returns, calendar, historic universe; **blocked**. M5/M12/M15 plus action policy, and original disclosure records where necessary.
- **Weaknesses/evaluation:** foreign evidence is not local validation; halts, limits, crashes, fees and unavailable shorts can destroy paper spreads. Compare implementable long-only ranks with equal weight and buy-and-hold in walk-forward tests.
- **Complexity/evidence:** **high; Foreign empirical + Statistic**. S9 construction; S10 accessed US working-paper abstract; neither establishes an Iranian premium.

### C5. Moving-average trend benchmark

- **Purpose/rationale:** provide a simple, interpretable technical baseline rather than an unexamined indicator library.
- **Calculation:** `SMA_h(t)=Σ_(s=t−h+1..t)p_s/h`; rule `1(p_t>SMA_h(t))` or prespecified short/long crossover; prices, adjustment and execution timing fixed in advance.
- **Inputs/availability/sources:** verified adjusted prices and session states; **blocked**. M5/M12/M15 provide enrichment leads.
- **Weaknesses/evaluation:** lag, whipsaws, stale closes and limit-locked sessions; many horizons invite selection bias. Compare frozen horizons with buy-and-hold after costs and conservative fills; count every tried variant.
- **Complexity/evidence:** **medium/high; Statistic + Heuristic trading rule**. Arithmetic averaging; methods #22. No accessed Iranian predictive evidence. RSI/MACD/ATR can be future separately specified candidates if this benchmark and price contract justify expansion.

## D. Sector and industry analysis

### D1. Sector transfer, participation and breadth

- **Purpose/rationale:** show whether observed category transfer is concentrated in particular industries.
- **Calculation:** `N_g=Σ_(i∈g)N_i`, `I_g=N_g/Σ_(i∈g)T_i`; sector active-sign breadth uses A2. Retain unclassified rows in a separate coverage bucket.
- **Inputs/availability/sources:** values exist; **blocked as sector analysis** until dated instrument-to-sector mapping. M4 exposes one current sector; historical dictionaries/membership remain unverified.
- **Weaknesses/evaluation:** funds, rights, holding companies and changing memberships complicate comparability. Reconcile classified sector totals to covered population; audit mappings and show missing value share. Not a sector-return forecast.
- **Complexity/evidence:** **medium; Identity + Heuristic grouping**. Arithmetic; M4 proves possible field access, not historical classifications.

### D2. Sector participation rotation

- **Purpose/rationale:** distinguish a change in trading allocation from a change in total activity.
- **Calculation:** `s_g,t=T_g,t/Σ_g T_g,t`; rotation `Δs_g=s_g,t−s_g,t−h` on a declared stable classification/universe. Optionally compare sector transfer intensities, without calling them returns.
- **Inputs/availability/sources:** checked historical values and dated sectors; **blocked by mapping**. Future M4-based master and calendar adapter.
- **Weaknesses/evaluation:** mapping changes, large blocks and mixed assets mimic rotation; rising traded-value share does not prove portfolio reallocation or performance leadership. Compare matched constituents, dominant-name exclusions and fixed lookbacks; future-return evaluation requires H4.
- **Complexity/evidence:** **medium; Heuristic**. Explicit share-change definition; no accessed empirical validation of this exact Iranian rule.

### D3. Sector-relative flow and robust dispersion

- **Purpose/rationale:** identify an instrument's unusual participation relative to economically similar peers.
- **Calculation:** `u_i=I_i−median_(j∈g)I_j`; optionally divide by sector MAD with declared scaling and minimum peers. Zero MAD yields unavailable standardized score.
- **Inputs/availability/sources:** checked bounded I plus dated peer groups; **blocked by sectors**. M4 identity/classification and S3 statistic.
- **Weaknesses/evaluation:** small/heterogeneous sectors produce unstable comparisons; contemporaneous peer adjustment is descriptive. Audit peer counts, leave-one-out medians and turnover strata. Future signals must use available memberships and separate outcome dates.
- **Complexity/evidence:** **medium; Statistic + Heuristic application**. S3 establishes MAD, not sector-neutral alpha.

### D4. Sector-return attribution and relative leadership

- **Purpose/rationale:** explain portfolio/market outcomes by industry rather than confuse high flows with realized performance.
- **Calculation:** with lagged weights, sector contribution `c_g,t=Σ_(i∈g)w_(i,t−1)r_i,t`; excess sector return `R_g−R_benchmark`, with explicit rebalancing and cash treatment.
- **Inputs/availability/sources:** dated classifications, prices/actions, portfolio/index weights and benchmarks; **blocked**. M4/M5/M12/M15 and index-provider history are future sources; histories not verified in this audit.
- **Weaknesses/evaluation:** price versus total-return mismatch and current sector weights create bias. Contributions must sum to portfolio return including cash/cost components; compare equal/value-weight specifications and fixed classification dates.
- **Complexity/evidence:** **high; Identity/Statistic**. Weighted-return arithmetic; no predictive sector-rotation evidence claimed.

## E. Liquidity and market microstructure

### E1. Amihud-style illiquidity

- **Purpose/rationale:** approximate large price movement per unit of traded value, a rough liquidity proxy.
- **Calculation:** `ILLIQ_h=mean(|r_t|/T_t)` across declared eligible days and stated currency units. Daily/archive-window adaptation differs from the source's annual averaging.
- **Inputs/availability/sources:** T exists; adjusted returns and scope matching do not; **blocked**. M5/M12/M15 and action checks.
- **Weaknesses/evaluation:** not bid–ask spread or causal impact; zero trading, price limits, blocks and inflation distort it. Compare within class/size, disclose excluded days and currency scaling; test incremental out-of-sample associations conservatively.
- **Complexity/evidence:** **medium/high; Foreign empirical**. S25 original author working paper full text accessed; journal metadata only. No local effect established.

### E2. Share/free-float turnover and normalized transfer

- **Purpose/rationale:** distinguish active trading from activity relative to the security's available supply.
- **Calculation:** `τ=Q/sharesOutstanding` or `Q/freeFloatShares`; quantity transfer ratio `(qRB−qRS)/freeFloatShares`. Numerators and denominators need matching dated units.
- **Inputs/availability/sources:** quantities exist, dated shares/float absent; **blocked**. M4 current outstanding-quantity field is a lead, not historic float; capital changes require action/disclosure records.
- **Weaknesses/evaluation:** repeated intraday turnover is not distinct ownership change; float estimates may be stale. Reconcile split/capital changes and publication lags; compare with raw T and same-class instruments.
- **Complexity/evidence:** **medium; Identity + Heuristic interpretation**. Arithmetic; methods #26; no “true liquidity” claim from a ratio alone.

### E3. Quoted spread, depth and book imbalance

- **Purpose/rationale:** measure currently available displayed liquidity separately from executed ownership transfer.
- **Calculation:** best spread `ask−bid`, relative spread `2(ask−bid)/(ask+bid)`; level-k depth imbalance `(ΣbidQty−ΣaskQty)/(ΣbidQty+ΣaskQty)` at synchronized timestamps, positive denominator.
- **Inputs/availability/sources:** timestamped historical quotes/levels, verified sides, units and states; **blocked**. M10 observed current levels; S21 examines actual order-book events.
- **Weaknesses/evaluation:** quotes cancel, hidden liquidity exists, stale/asynchronous levels mislead. Displayed imbalance is not guaranteed execution or spoofing evidence. Validate book/print consistency, durations, locked/crossed states and subsequent realized fills; only then test short-horizon relations.
- **Complexity/evidence:** **high; Statistic + Foreign empirical motivation**. S21's US event-level evidence does not validate daily category imbalance.

### E4. Limit-state, halt and execution-availability diagnostics

- **Purpose/rationale:** detect when a correct signal could not plausibly be traded.
- **Calculation:** match instrument/session prices with dated thresholds and states; flag prints at a bound separately from observed unmatched queue. Record time in verified halt/limit states; simulated fill depends on actual phase, side, depth and conservative order-priority assumptions.
- **Inputs/availability/sources:** prices, thresholds, timed states/books and operative rules; **blocked**. M5/M6 show one bound-trading sample; M11 failed to establish dated status; M3/M13 rule content unresolved.
- **Weaknesses/evaluation:** all-day upper-bound trades do not establish an unfilled buy queue. Today's bands/base volume cannot be applied historically. Manual event replay, no-fill stress tests and dated-rule checks are mandatory.
- **Complexity/evidence:** **high; official observations + Heuristic simulation**. M3–M6/M11/M13; no universal limit or fill assumption.

## F. Statistical and quantitative analysis

### F1. Flow autocorrelation and serial-dependence diagnostics

- **Purpose/rationale:** test whether current flow behavior differs from uncorrelated noise before forecasting it.
- **Calculation:** `ρ_k=Corr(I_t,I_(t−k))`; Ljung–Box `Q=n(n+2)Σ_(k=1..m)ρ_k²/(n−k)` under its test assumptions, declared m and degrees of freedom.
- **Inputs/availability/sources:** aligned valid historical intensities; **conditional now**. Verified session gaps/identities improve interpretation; no price substitute needed.
- **Weaknesses/evaluation:** persistence may be reporting structure or constrained price discovery; rejecting a serial-correlation null is not profitable predictability. Guard constant/short series; compare regimes and dependence-aware holdout forecasting against simple baselines.
- **Complexity/evidence:** **medium; Statistic**. S4/S5 documentation; not local return evidence.

### F2. Residual flow, rank IC and incremental explanatory value

- **Purpose/rationale:** assess whether flow adds beyond size, momentum and liquidity rather than rediscover their effects.
- **Calculation:** per-date model `I_i=a+b log(ME_i)+c log(1+ILLIQ_i)+d Momentum_i+sectorEffects+u_i`; rank u. Later `IC_t=Spearman(u_i,t,r_i,future)` with explicit post-availability target interval.
- **Inputs/availability/sources:** checked flow now; required controls/returns absent, so **blocked for intended model**. Value-only descriptive controls are a separately named reduced experiment. M4/M5/M12/M15, CODAL M8, S20 implementation.
- **Weaknesses/evaluation:** controls can be noisy/endogenous; fitted coefficients are not causal; tiny cross-sections overfit. Fit preprocessing/selection within training, evaluate incremental held-out IC/net long-only outcomes and log all alternatives.
- **Complexity/evidence:** **high; Heuristic using established regression**. S20; S14 motivates liquidity distinctions, not this exact flow factor.

### F3. Entropy and Jensen–Shannon participation shift

- **Purpose/rationale:** supplement HHI with tail-sensitive concentration and changes in activity distribution.
- **Calculation:** nonnegative weights `p_i=T_i/ΣT`; entropy `H=−Σp log p`, effective count `exp(H)`; on common support, `m=(p+q)/2`, `JS=½Σp log(p/m)+½Σq log(q/m)`. Define `0log0=0`; positive totals required.
- **Inputs/availability/sources:** checked values; **now with explicit matched support/coverage**. Identity enrichment needed for economic continuity.
- **Weaknesses/evaluation:** changed coverage can mimic redistribution; SciPy JS distance is square root of JS divergence. Check equal/single weights, symmetry, identical distributions, declared log base and lost coverage. Compare with HHI and dominant-name removal before adding complexity.
- **Complexity/evidence:** **medium; Statistic + Heuristic application**. S2/S19.

### F4. EWMA baseline and residual activity

- **Purpose/rationale:** describe recent flow changes with a transparent trailing baseline.
- **Calculation:** `m_t=αI_t+(1−α)m_(t−1)`, `α=2/(span+1)` with explicit initialization; surprise `I_t−m_(t−1)`. Missing-session policy and span are fixed parameters.
- **Inputs/availability/sources:** historical intensities; **conditional now**. Calendar and availability required for predictive framing.
- **Weaknesses/evaluation:** smoothing lags regime changes and does not itself remove seasonality; alternative spans increase trial counts. Verify recursion and gaps; compare held-out flow MAE with lag-one and trailing-median baselines, not just visually appealing curves.
- **Complexity/evidence:** **medium; Statistic + Heuristic application**. S24 documents recursion; no alpha evidence.

## G. Fundamental analysis

### G1. Valuation and size/value ranks

- **Purpose/rationale:** compare price with available earnings/book equity, and test whether flow is confounded by firm scale or valuation.
- **Calculation:** `ME=price×shares`, `P/E=ME/TTMearnings` only with compatible equity/share scope and positive earnings; `B/M=bookEquity/ME`. Distinguish undefined/negative earnings rather than ranking negative P/E as cheap.
- **Inputs/availability/sources:** point-in-time statements, prices, shares and dates; **blocked**. CODAL M8 original versions plus M4/M5; historical statement contents not yet audited.
- **Weaknesses/evaluation:** restatements, fiscal calendars, inflation and consolidated versus parent scope matter. Recompute manually from originals, apply publication lag and compare sector-aware held-out ranks; factor replication requires fixed eligible universes/breakpoints.
- **Complexity/evidence:** **high; Statistic + financial hypothesis**. S8 defines size/value construction; accessed library data do not prove Iranian value premiums.

### G2. Profitability and investment factors

- **Purpose/rationale:** investigate earnings capacity and asset growth as complementary dimensions to price/value.
- **Calculation:** French-style `OP=(Revenue−COGS−Interest−SG&A)/BookEquity`; `Inv=(Assets_(y−1)−Assets_(y−2))/Assets_(y−2)`. Component definitions, nonpositive bases and fiscal alignment must be explicit.
- **Inputs/availability/sources:** original published statement vintages and dated equity universe; **blocked**. M8 CODAL attachments need independent adapters and accounting validation.
- **Weaknesses/evaluation:** missing components are not zero; OP is not automatically reported operating margin. Inflation/currency and industry business models limit comparisons. Validate statement identities and incremental held-out associations versus size/value/momentum, with multiple-testing controls.
- **Complexity/evidence:** **high; Statistic + research hypothesis**. S11–S13 are accessed source constructions; underlying empirical articles/local effects not established here.

### G3. Earnings quality and accruals hypothesis

- **Purpose/rationale:** distinguish accounting earnings from cash generation as a prospective research dimension.
- **Calculation:** an explicitly chosen simple cash-flow accrual ratio `A=(netIncome−cashFlowFromOperations)/mean(totalAssets_start,totalAssets_end)`, requiring compatible periods, scope and positive asset denominator. This is one definition, not interchangeable with balance-sheet accrual variants.
- **Inputs/availability/sources:** point-in-time income, cash-flow and balance-sheet statements; **blocked**. M8 provides disclosure discovery, not an audited statement contract.
- **Weaknesses/evaluation:** working-capital seasonality, financial-company cash flows, classification changes and inflation can dominate. Reconcile all statement periods/units and test whether the preregistered rank adds beyond profitability, sectors and size on later data.
- **Complexity/evidence:** **high; Heuristic research candidate**. Arithmetic and M8 source availability only; no accessed accrual-premium paper or Iranian predictive result is claimed. Literature review is a prerequisite before promoting this candidate.

### G4. Disclosure-event and correction studies

- **Purpose/rationale:** study reactions to financial disclosures and distinguish original news from revisions.
- **Calculation:** define publication event and first feasible reaction interval; cumulative abnormal return `CAR=Σ_(event window)(r_i−E[r_i|past benchmark model])`, with event overlap and estimation window specified. Compare transfer/turnover responses separately.
- **Inputs/availability/sources:** original disclosure/correction timestamps, text/event labels, returns, benchmark, halts; **blocked**. M8 proves sent/published/correction metadata exists; timezone/action/execution histories still needed.
- **Weaknesses/evaluation:** concurrent news, endogenous timing, halted securities and later corrections confound attribution. Audit sample labeling, timezone and pre-event trends; use placebo dates and clustered/dependence-aware uncertainty. CAR is not causal proof.
- **Complexity/evidence:** **high; Statistic + Heuristic event application**. M8; S20 regression infrastructure, without claiming an accessed event-study empirical paper.

## H. Trading strategies and backtesting

### H1. Ownership-flow sort experiment

- **Purpose/rationale:** test, rather than assume, that ownership transfer contains incremental return information.
- **Calculation:** form ranks from C3 or prespecified lagged B2; compare next-eligible-period total returns of frozen quantiles. A long-short difference is a research diagnostic; initial investable strategy should be long-only with explicit cash/unfilled positions.
- **Inputs/availability/sources:** prices/actions, historical equity universe, publication ledger and execution constraints; **blocked**. M4–M6/M8/M12–M15 plus verified fees/state history.
- **Weaknesses/evaluation:** publication often follows the report session; same-close fills are invalid. Follow-institutions/popular tablokhani narratives are unverified. Use H4, match momentum/liquidity/size baselines and show capacity, turnover and no-fill sensitivity.
- **Complexity/evidence:** **high; Heuristic**. Methods #20; V1–V3 statistical safeguards, not support for alpha.

### H2. Price-momentum/trend baseline strategy

- **Purpose/rationale:** establish whether a more complex flow model adds anything beyond a transparent price-only rule.
- **Calculation:** freeze C4 or C5, select lagged eligible holdings at scheduled rebalance, execute next permitted phase after signal availability; track drifted weights, cash, costs and actual assumed fills.
- **Inputs/availability/sources:** adjusted returns, price/state/rule histories and dated costs; **blocked**. M5/M6/M12–M15; dated authoritative rules still unresolved.
- **Weaknesses/evaluation:** many lookbacks and favorable fill choices create apparent success. Compare identical universe/schedule with H3 and cash; assess holdouts, period stability, drawdowns and costs, counting each variant.
- **Complexity/evidence:** **high; Foreign empirical motivation + Heuristic implementation**. S9/S10 concern foreign momentum; C5 trend is an unvalidated local hypothesis.

### H3. Investable equal-weight benchmark

- **Purpose/rationale:** supply a fair, feasible baseline before optimizing portfolios or promoting strategies.
- **Calculation:** target `w_i=1/n` among historical eligible holdings at rebalance; daily `R_p=Σw_(i,t−1)r_i,t` with weights drifting between rebalances, plus cash, costs and constraints. Unknown returns do not justify dropping a holding and renormalizing.
- **Inputs/availability/sources:** total returns, listings/delistings, dated universe and execution data; **blocked**. M4/M5/M12/M15 and authoritative delisting/cash-event records.
- **Weaknesses/evaluation:** frequent rebalancing is costly; inaccessible stocks create residual cash. Reconcile cash/position ledger, corporate actions and wealth recursion; use the same eligibility/fill model as the candidate strategy.
- **Complexity/evidence:** **high; Identity/Statistic**. Portfolio arithmetic; methods #32; benchmark is not an optimality claim.

### H4. Nested walk-forward, dependence and search-bias controls

- **Purpose/rationale:** assess whether apparent usefulness survives realistic selection and chronology.
- **Calculation:** group all instruments by decision date; select only in inner chronological folds; evaluate frozen choice in later outer blocks and untouched final holdout. Purge unresolved/overlapping target intervals; log every trial; use date-block uncertainty and an appropriate preregistered multiplicity method. DSR/PBO/Reality Check require their own assumptions and full search ledger.
- **Inputs/availability/sources:** point-in-time signals, targets, trial history and enough sessions; **design ready, empirical use blocked**. Current data can support limited flow-behavior holdouts, not return strategies.
- **Weaknesses/evaluation:** ordinary time splitting does not repair revised vintages, cross-sectional leakage or invented fills. Test interval boundaries and leakage traps; report negative results and economic baselines.
- **Complexity/evidence:** **high; established statistical research**. V1–V4/V7, S6/S18; see full [protocol](validation-protocol.md).

## I. Risk management and portfolio analysis

### I1. Volatility, drawdown and downside exposure

- **Purpose/rationale:** quantify loss paths and variability without confusing transfer changes with investment risk.
- **Calculation:** `σ=sd(r,ddof=1)`; optional `σannual=σ√A` with a justified local session convention. `W_t=Π(1+r_s)`, `DD_t=W_t/max_(u≤t)W_u−1`, `MDD=min DD`. Report period and unannualized measures.
- **Inputs/availability/sources:** action-aware returns/portfolio wealth and calendar; **blocked**. M5/M12/M15 plus verified corporate-action/cash treatment.
- **Weaknesses/evaluation:** stale/limit-constrained prices understate immediate risk; daily drawdown misses intraday losses. Check hand-calculated wealth paths and identical benchmark windows; include cash/costs, halt exposure and sensitivity to stale observations.
- **Complexity/evidence:** **medium/high; Statistic/Identity**. Methods #23–24; V4 cautions about simplistic risk/performance inference, not local calibration.

### I2. Shrinkage minimum-variance portfolio

- **Purpose/rationale:** investigate risk reduction with a more stable covariance estimate than an unrestricted sample matrix.
- **Calculation:** `Σsh=(1−δ)Σsample+δμI`, `μ=tr(Σsample)/n`, δ estimated by a declared method; minimize `w'Σsh w` with `Σw=1`, `w≥0`, concentration/turnover constraints.
- **Inputs/availability/sources:** aligned adjusted returns and investable histories; **blocked**. Price/action/identity adapters plus execution model.
- **Weaknesses/evaluation:** noisy/stale correlations, regime changes and estimation costs can overwhelm model benefits. Train covariance only on past data; compare out-of-sample volatility, concentration, turnover, costs and drawdowns with H3/I3.
- **Complexity/evidence:** **high; Statistic**. S15 shrinkage documentation; S16/S17 open-source implementation references, not guarantees of future risk reduction.

### I3. Inverse-volatility allocation baseline

- **Purpose/rationale:** provide a simple risk-scaling alternative for comparison with optimizers.
- **Calculation:** positive trailing `σ_i` only; `w_i=(1/σ_i)/Σ_j(1/σ_j)` with declared caps and rebalance rule. Zero/stale volatility produces ineligible or explicit fallback state, not infinite weight.
- **Inputs/availability/sources:** verified trailing returns, historical eligible universe and costs; **blocked**. Same sources as I1/H3.
- **Weaknesses/evaluation:** ignores correlations and can crowd into stale or constrained assets; not general equal-risk-contribution/risk parity. Test analytical weights, caps and zero-volatility cases; compare realized risk and turnover with equal weight on identical data/fills.
- **Complexity/evidence:** **medium/high; Heuristic allocation**. Explicit arithmetic; methods #34; no accessed local performance evidence.

### I4. Liquidity capacity and execution stress scenarios

- **Purpose/rationale:** expose strategies whose paper gains depend on trading too much or exiting constrained holdings.
- **Calculation:** planned-order value divided by contemporaneous eligible trading value, with a predeclared participation cap; simulate fees/slippage scenarios, partial/no fills, delayed exits and cash settlement. Report scenario distributions, not a falsely precise impact prediction.
- **Inputs/availability/sources:** T exists; order plans, dated scope, states, books, fees and settlement rules absent; **blocked as an executable assessment**. M3/M6/M10/M13/M14; V5 impact framework motivates the risk/cost tradeoff.
- **Weaknesses/evaluation:** daily volume does not guarantee side-specific fill or queue priority; universal square-root/linear impact constants are unjustified. Reconcile ledger, stress zero turnover/locked limits and compare conservative versus optimistic assumptions.
- **Complexity/evidence:** **high; Heuristic scenarios with theoretical motivation**. V5 assumptions are not calibrated to Iran; M14 bulletin is not a universal cost constant.

## J. Anomaly detection and emerging research opportunities

### J1. Trailing robust activity/flow anomalies — second-milestone candidate

- **Purpose/rationale:** surface unusual observed behavior for investigation without calling it a trade recommendation.
- **Calculation:** for `x=I` or `log(1+T)`, `z_t=0.67448975[x_t−median(x_past)]/MAD(x_past)`, strictly excluding the current observation from baseline. Declare lookback, minimum coverage and degenerate-baseline handling.
- **Inputs/availability/sources:** historical checked values; **conditional now** with session/coverage disclosures. Calendar/identity enrichment improves comparability.
- **Weaknesses/evaluation:** MAD=0 gives unavailable score, never epsilon fabrication; thresholds are heuristics, not probabilities. Regimes, mixed classes and reporting errors trigger alerts. Use synthetic outlier/constant-window tests and manually adjudicated historical alert samples; later evaluate subsequent flow outcomes against baselines.
- **Complexity/evidence:** **medium; Statistic + Heuristic alert**. S3; no predictive claim.

### J2. Reconciliation and cross-sheet anomaly detection

- **Purpose/rationale:** distinguish a genuine market observation from a unit/header/scope or revision problem before ranking it.
- **Calculation:** report value/quantity residuals independently; compare mapped detail totals, compatible footers and duplicate representations; flag contradictory units, ambiguous roles and overlapping rows rather than force agreement. A per-metric eligibility mask retains independently checked fields.
- **Inputs/availability/sources:** raw workbook/cell provenance and existing parser/audit; **now for daily tables**. Hidden/BI/monthly adapters require separate scope validation before extending comparisons.
- **Weaknesses/evaluation:** footer mismatches may be different populations, not corruption; blank hidden cells are not zero. Test shifted/institution-first headers, duplicates, explicit zeros versus missing, scaled percentages and tolerance boundaries. Preserve raw values and reason codes.
- **Complexity/evidence:** **low reuse, medium extension; Identity/data quality**. [Inventory](dataset-inventory.md); existing audit supplies evidence, not universal auxiliary-sheet validation.

### J3. Counterflow cancellation — first milestone

- **Purpose/rationale:** distinguish an aligned category-transfer day from large offsetting transfers hidden by a small aggregate net.
- **Calculation:** `G=Σ|N_i|`; `C=1−|ΣN_i|/G` for `G>0`; else unavailable. By triangle inequality `0≤C≤1`. Display G, net, population and `G/ΣT` where valid. This bound does not require exact institutional counterpart conservation.
- **Inputs/availability/sources:** complete checked value table for full-population claim; **now**. Partial labeled observations may produce only an explicitly partial descriptor.
- **Weaknesses/evaluation:** high cancellation can accompany trivial activity and is not systemic risk, capital flight or investor disagreement. Test all-aligned, equal-opposite, all-zero and scale-invariance fixtures; compare with breadth/concentration and dominant-instrument removal.
- **Complexity/evidence:** **low; proposed descriptive construction**. Explicit algebra/triangle inequality; methods #13. No source is claimed to validate this exact statistic as a trading signal.

### J4. Structural shifts and reporting-regime research

- **Purpose/rationale:** investigate whether changing flow/activity distributions reflect market behavior, coverage or source-process changes.
- **Calculation:** compare fixed past/current windows of matched-support I/T distributions, medians/MAD and F3 JS; track schema, parser, revision and coverage breakpoints beside behavioral changes. Any change detector/threshold must be separately specified and fitted using earlier data.
- **Inputs/availability/sources:** historical exact rows, layouts, provenance; **conditional now for descriptive comparisons**. Dated rules, calendar, identity, inflation/FX release vintages needed for causal/economic attribution; official macro histories not yet retrieved.
- **Weaknesses/evaluation:** multiple testing and post-hoc event stories invite false discovery; deterministic schema changes can masquerade as market regimes. Inject synthetic shifts, inspect false alerts around known parser/report changes, require matched coverage and out-of-time monitoring. No automatic causal label.
- **Complexity/evidence:** **medium/high; Heuristic research application**. S3/S19/V1–V3 provide statistics/search safeguards, not evidence of an Iranian trading regime model.

## Recommendation and research backlog

The first vertical slice combines **A1, A2, A3 and J3**, with **J2** as an eligibility/provenance prerequisite. Reuse existing parsing and validation; produce deterministic exact-source JSON/CSV/Markdown, explicit denominators and ranked descriptive contributors. No new participant counts, price fields, sector labels or forecasts are required. At the user's request, the milestone includes existing-webapp snapshot views and report downloads backed by the same deterministic artifacts. User approval of the architecture and implementation plan precedes analytical code.

Next consider **A4/J1/B4** for coverage-aware historical investigation, then a narrowly scoped identity/calendar/price/action/availability pilot. Promote sector, fundamental, factor and portfolio opportunities only after their stated data gates pass. Defer broad technical-indicator libraries, opaque ML and claimed smart-money signals until simpler benchmarks and point-in-time evaluation justify them. Account-level herding/holdings concentration, VPIN, aggressive order-flow measures and manipulation claims cannot be reconstructed by renaming these daily category aggregates.

This catalog is broad enough to guide staged research, not an assertion of exhaustive literature coverage. Accruals, local fundamental/sector hypotheses, exact operative exchange rules and local causal mechanisms require further primary research before implementation or empirical claims. Discovery should continue through the reusable research skills and a recorded hypothesis/trial ledger; a negative result or blocked data contract is a useful outcome.
