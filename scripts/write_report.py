"""Build a readable research note from analyze_reports.py outputs."""
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
x = json.loads((ROOT / 'reports/highlights.json').read_text())
days = x['days']
latest = days[-1]
previous = days[-2]


def toman(value):
    return float(value) / 1e13


def signed(value):
    return f'{toman(value):+.3f}'


def rank_table(records, cumulative=False):
    text = '| Exact symbol | Company / instrument name | Individual net purchases, trillion toman |'
    if cumulative:
        text += ' Positive / observed days |'
    text += '\n|---|---|---:|' + ('---:|' if cumulative else '') + '\n'
    for r in records[:5]:
        text += f"| {r['symbol']} | {r['company']} | {signed(r['retail_net_rial'])} |"
        if cumulative:
            text += f" {r['positive_days']} / {r['days']} |"
        text += '\n'
    return text


recent5 = sum(float(d['retail_net_rial']) for d in days[-5:])
total_net = sum(float(d['retail_net_rial']) for d in days)
mean_previous = statistics.mean(float(d['turnover_rial']) for d in days[:-1])
manifest = json.loads((ROOT / 'data/download-manifest.json').read_text())
lines = [f'''# Findings from TSE market-performance workbooks

Analyzed {len(days)} downloaded daily reports, {days[0]['date']}–{latest['date']} (Solar Hijri), covering {sum(d['symbols'] for d in days):,} instrument-day rows. The latest report is dated 10 November 2026 and was published on 11 November. This is a recent sample, not the full archive: the category API reported 802 entries when retrieved on 11 November 2026. The broader keyword search returned 1,031 entries across categories.

## Main findings

1. **Individual net buying strengthened recently.** Across every instrument row in these files, the latest five reports total **{signed(recent5)} trillion toman** of individual net purchases. The full 20-report sample totals **{signed(total_net)} trillion toman**, with positive individual net purchases on {sum(float(d['retail_net_rial']) > 0 for d in days)} of 20 days. The recent direction differs from the full-period direction.
2. **The latest day shows broad ownership transfer toward individuals.** Individual net purchases were **{signed(latest['retail_net_rial'])} trillion toman** across {latest['symbols']:,} instrument rows: {latest['retail_net_positive_symbols']} positive, {latest['retail_net_negative_symbols']} negative, and {latest['retail_net_zero_symbols']} zero. Among nonzero rows, {latest['retail_net_positive_symbols']/(latest['retail_net_positive_symbols']+latest['retail_net_negative_symbols']):.1%} were positive. This measures ownership-flow breadth, not price-return breadth or the number of distinct companies.
3. **Latest-day activity increased.** Reported trading value was **{toman(latest['turnover_rial']):.2f} trillion toman**, {float(latest['turnover_rial'])/float(previous['turnover_rial'])-1:.1%} above the prior report and {float(latest['turnover_rial'])/mean_previous-1:.1%} above the preceding 19-report mean. These totals include the workbook's mixed instrument universe.
4. **Trading is concentrated.** The ten largest exact symbol rows account for **{float(latest['top10_turnover_share']):.2%}** of latest-day reported trading value. A rise in total trading value can therefore come from a handful of instruments. An asset-class mapping is needed before treating this as equity-market liquidity.
5. **A strong day can contradict a longer pattern.** On the latest day, individual net purchases in فولاد1 were +0.384 trillion toman and in وبملت1 +0.590 trillion toman. Across the 20-report sample, those same exact rows show individual net sales of approximately 6.035 and 2.386 trillion toman, respectively. This supports monitoring a possible reversal; it does not establish that a lasting reversal has occurred.

## Latest-day largest individual net purchases

{rank_table(x['latest_top_retail_net_buys'])}
## Latest-day largest individual net sales

Negative numbers mean individuals sold more than they bought; institutions were net buyers by the same amount.

{rank_table(x['latest_top_institutional_net_buys'])}
## Largest cumulative individual net sales over the sample

{rank_table(x['cumulative_top_institutional_net_buys'], True)}
## Daily comparison

All values below are trillion toman. Positive net purchases mean ownership transferred toward individuals.

| Report date | Reported trading value | Individual net purchases | Positive / negative instrument rows |
|---|---:|---:|---:|
''']
for d in days:
    lines.append(f"| {d['date']} | {toman(d['turnover_rial']):.3f} | {signed(d['retail_net_rial'])} | {d['retail_net_positive_symbols']} / {d['retail_net_negative_symbols']} |\n")
lines.append(f'''
## What the files can support

- **Ownership-transfer screens:** rank institutional or individual net buying in rials and volume. Normalize net purchases by the instrument's daily trading value so that large and small instruments can be compared; also apply a minimum turnover threshold.
- **Persistence and reversals:** calculate rolling 5/10/20-report net purchases, positive-day counts, and changes relative to an instrument's own baseline. Missing observations are not assumed to be zero.
- **Liquidity and concentration:** track trading value, reported volume within compatible instrument types, top-N trading shares, and unusual activity relative to history.
- **Execution-price comparisons:** divide each investor category's purchase/sale value by its corresponding volume to obtain an implied average execution price. This is not an end-of-day price or a measure of future performance.
- **Asset-class or sector rotation after enrichment:** join symbols to authoritative instrument types and sector classifications, then compare flows within those groups. Company names alone are insufficient for a reliable classification.

## Essential interpretation limits

**Individual means حقیقی; institutional means حقوقی.** These are legal investor categories. An institutional buyer is not automatically an informed investor; a fund's market maker can be classified as institutional.

**Net purchases are ownership transfer, not new cash entering the exchange.** Every purchase has a seller. Individual net purchases equal institutional net sales within this two-category accounting. Summing the absolute value of both sides would double-count the transfer. Secondary-market fund flows also do not establish fund creation/redemption flows.

**The summary percentages and all-row totals use different apparent scopes.** On {latest['date']}, the summary cells I16/I17 label individual purchase/sale shares for “سهام و حق تقدم” as **{float(latest['summary_retail_buy_share']):.2%} / {float(latest['summary_retail_sell_share']):.2%}**. Aggregating the complete detailed value table produces **{float(latest['retail_buy_value_share']):.2%} / {float(latest['retail_sell_value_share']):.2%}**. The detailed table includes funds and other instruments. We have not reconstructed the summary's exact eligibility rules. Do not multiply the summary percentage gap by the workbook-wide trading-value total to estimate equity net purchases. The findings above use the detailed table consistently.

**Retain symbol suffixes and check identity changes.** Symbols ending in 1, 2, 3, or 4 are retained separately; their market/trade types have not been independently mapped. The sample also contains both شبريز1 and شتبريز1 on different dates. An authoritative identifier history is needed to determine whether labels should be joined; exact-label cumulative rankings can otherwise split an issuer's history.

**No return forecast or valuation conclusion follows from these files alone.** They contain no closing-price return series, index comparison, market cap/free-float denominator, sector map, P/E history, investor counts, or intraday order-book sequence. In particular, the popular per-capita buyer/seller “power” metric cannot be calculated without investor counts. Testing whether flows predict returns requires price data, corporate-action adjustments, publication-time alignment, and transaction-cost assumptions. Report dates precede publication, so same-day use in a backtest would introduce look-ahead bias.

**Units:** source value columns are rials; 10 rials = 1 toman; 10^13 rials = 1 trillion toman. Source volume is not assumed to represent comparable shares across every instrument class. Monetary values are nominal and not inflation- or FX-adjusted.

## Retrieval and validation

The downloader uses the same public API invoked by [TSE's download center](https://www.tse.ir/download-center):

- List: `https://webgw.tse.ir/cmssite/api/v1/EDeliveryObject/List/fa?EDeliveryCategoryIds=12&PageNumber=1&PageSize=20`
- Report detail: `EDeliveryObject/Find/{{report_id}}`; download the returned Excel attachment link.
- Latest report: [{manifest[-1]['title'].strip()}]({manifest[-1]['detail_url']}).

All 20 requested files downloaded without errors. The latest downloaded workbook has the same SHA-256 hash as the user-provided workbook: `1ef908416e6103d35d563efa19b2edd5bbd372cee6bbe6e02d9ebcecffac6b8a`.

For every analyzed instrument row, combined individual/institutional purchases equal sales in both value and volume. Summing the extracted rows reproduces the workbook summary's total value and volume on all 20 dates. Hidden sheets duplicate report data and are excluded from aggregation. Parsing reads stored Excel values, including cached formula results; it does not recalculate Excel formulas. These accounting checks establish internal consistency, not independent verification of the publisher's underlying trades.

## Files and reproduction

- [Downloaded Excel workbooks](../data/raw/)
- [Source URLs and publication dates](../data/download-manifest.json)
- [Daily summary CSV](daily-summary.csv)
- [Instrument-day flow CSV](symbol-flows.csv)
- [Cumulative exact-symbol flow CSV](cumulative-symbol-flows.csv)
- [Validation details](validation.json)

Run from the project folder:

```bash
python3 scripts/download_reports.py --limit 20
python3 scripts/analyze_reports.py
python3 scripts/write_report.py
```

The downloader accepts `--limit 0` for the entire category. Analyzing a longer archive may require adapting the parser to older workbook layouts. It reuses valid files already downloaded. The analysis includes every workbook present in `data/raw`.
''')
(ROOT / 'reports/market-insights.md').write_text(''.join(lines))
print('Wrote reports/market-insights.md')
