---
name: iran-market-backtesting
description: Use when simulating orders, fills, cash, costs or portfolio returns for Iranian securities, particularly around publication delays, halts, price limits and order queues.
---

# Iranian market backtesting reference

**Draft checkpoint: application-scenario validation remains pending; consult the reviewed research protocol and dated source evidence before relying on this reference.**

A signal observation is not an executable order. Use this reference only with point-in-time data and quantitative-validation; do not infer execution from daily ownership totals.

## Required source investigation

Retrieve dated operative SEO/TSE/IFB notices and clearing/fee schedules for the specific instrument type, venue, board and session. Record effective dates, supersessions and access limits. Check TSETMC instrument, price/state/threshold and corporate-action data against actual sessions; HTTP success/default records do not establish valid observations. Use CODAL original disclosure versions for event timing. The project's market-structure source register documents observed endpoints and unverified rules.

Never universalize a single instrument's current base volume, price limits, trading hours, costs, settlement cycle or borrowing availability. An informational fee compilation is a discovery source; operative notifications govern.

## Simulation contract

| Component | Required behavior |
|---|---|
| Information clock | Signal uses only available revisions; decision follows publication and processing, order follows decision, fill follows order in an eligible phase. |
| Orders/fills | Track pending, partially filled, filled, rejected and expired orders; enforce quantities, cash and position constraints. |
| Halts/limits | Halted session has no ordinary fill. A limit-locked price requires accessible opposing liquidity/queue evidence; daily high/low touching a price is not a fill guarantee. |
| Costs | Dated commissions, taxes, spread/slippage, minimums/caps, type/side applicability and settlement cash restrictions. |
| Corporate actions | Reconcile adjusted return series with actual units, dividends, rights, capital changes and executable unadjusted prices. Avoid double-counting adjustments. |
| Universe | Include delisted, suspended, renamed and unavailable instruments with dated mappings; unavailable exits retain position/risk. |

## Algorithm and validation

Process events chronologically: information -> decision -> order acceptance -> eligible market event -> supported fill -> costs/cash/position update -> valuation. State explicit open-order persistence, partial-fill allocation, exit and expiry policies. Unknown fill feasibility stays unfilled or is reported as a separately hypothetical scenario, never silently certain.

Test no-fill halts, queue limits, delayed publications, partial fills, stale prices, action dates, costs, cash conservation and missing exits. Compare gross/net results, drawdown, volatility, turnover, exposure, capacity and pessimistic execution scenarios against investable baselines. Almgren/Chriss provides execution-cost concepts, not calibrated Iranian parameters; obtain local evidence.

## Example and failures

A next-morning publication cannot buy at the preceding close. If the next eligible session is halted or limit-locked without opposing liquidity evidence, retain a pending/unfilled order under its explicit expiry policy; do not fabricate a close-price fill or erase the position when exit fails.

## Output

Produce the dated rule/source ledger, event/timestamp assumptions, order/fill/cash audit, gross/net benchmark comparison, sensitivity results and unsupported-data gates. Distinguish paper assumptions from observed fills. Live trading requires separate authorization.
