# TSETMC verification — 2026-11-15

Verified against the official API and the حقیقی-حقوقی tab on [شتران](https://www.tsetmc.com/instInfo/51617145873056483). Instrument metadata confirms this ID is شتران, Tehran Oil Refining, TSE (flow 1). All endpoints below returned HTTP 200 JSON during investigation; this is an undocumented API and availability/schema may change.

Base: `https://cdn.tsetmc.com/api/`.

| Endpoint | JSON key / use |
| --- | --- |
| `Instrument/GetInstrumentInfo/51617145873056483` | `instrumentInfo`: verify identity |
| `ClientType/GetClientType/51617145873056483/1/0` | `clientType`: current counts/volumes, **no actual values** |
| `ClientType/GetClientTypeHistory/51617145873056483` | `clientType`: dated history containing actual values |
| `ClientType/GetClientTypeHistory/51617145873056483/20261114` | `clientType`: one dated observation |
| `ClosingPrice/GetClosingPriceInfo/51617145873056483` | `closingPriceInfo`: current prices; use dated endpoint for collection |
| `ClosingPrice/GetClosingPriceDaily/51617145873056483/20261114` | `closingPriceDaily`: dated trade value/volume and prices |
| `ClosingPrice/GetMarketWatch` | `marketwatch`: instrument universe, no extra path suffix |
| `StaticData/GetStaticData` | Official security type descriptions |

ClientType values: `buy_I_Value`, `sell_I_Value`, `buy_N_Value`, `sell_N_Value`. I = individual (حقیقی), N = institutional (حقوقی). Corresponding volume fields end in `_Volume`; counts end in `_Count`. Identity/date fields are `insCode`, `recDate`; dated closing fields are `insCode`, `dEven`, `qTotCap` (rials), `qTotTran5J` (shares), `pClosing`, `pDrCotVal` (prices in rials).

## Actual-value check

| Date | Individual buy, rial | Individual sell, rial | Net, rial | Net, billion toman |
| --- | ---: | ---: | ---: | ---: |
| 1405/08/23 (2026-11-14) | 6,164,345,215,220 | 5,533,163,025,530 | 631,182,189,690 | 63.118218969 |
| 1405/08/24 (2026-11-15) | 2,304,817,507,370 | 175,593,634,670 | 2,129,223,872,700 | 212.92238727 |

Official page history displays these values in rounded billions of rials (for example 6,164.345 and 5,533.163 on 23/08). Counts and volumes also matched the dated API. On 23/08 total volume was 1,193,245,339, closing price 6,540 and last trade 6,640 rials. On 24/08 closing price was 6,730 rials. This establishes a sample match, not independent certification of every market instrument.

An overlap check for 1405/08/19 found شتران1 individual buy value matched the Excel archive at 2,118,070,430,520 rials, while individual sell differed: Excel 511,601,295,810 versus TSETMC 512,101,585,380. The discrepancy is 500,289,570 rials; its cause is unproven. Retain both sources and do not silently rewrite archive values.

## Aggregation scope

MarketWatch fields: `insCode` ID, `lva` ticker, `lvc` company, `insID` trading identity, `flow` market, `yVal` security type. Select flows 1 (TSE), 2 and 4 (IFB and base market). Supported types: 300/303/309/313 shares, 400/403/404 rights, 305 funds. Select only identities ending in 1, excluding secondary/block trade variants. Initial universe: 493 TSE and 581 IFB instruments (1,074 total), including 292 funds. Market membership and counts can change.

Each date is collected per instrument using dated endpoints, then reconciled before separate market aggregation. Historic primary aliases are the official ticker plus `1`; original suffixes remain distinct. This mapping was checked against archive tickers, but automatic rename joins are deliberately avoided. Current-universe membership introduces survivorship limits for older backfills. Excluding funds changes the same underlying rows for every analytics view and export.

No actual-value field means no exact flow; do not silently substitute `(individual buy volume - individual sell volume) × closing price`. Missing records are reported as exclusions, not zero or stale values.

Fund classification additionally uses type 380 commodity funds and fund-labelled type 306 records, solely for hiding their archive rows. This does not add commodity trades to the TSE/IFB feed. An identified fund’s observed numeric trade suffixes share its fund classification; their trade data remains separate.

## Mofid EasyTrader reference check — 2026-11-16

Compared the user's saved شتران screenshot (local reference; excluded from Git because it includes account details) for **1405/08/24** with a fresh response from `ClientType/GetClientTypeHistory/51617145873056483/20261115` and the deployed SQLite active snapshot for that same day. Individual buy/sell values, actual net value, total volume and net individual volume matched exactly between SQLite and TSETMC.

| Metric | Recomputed from official data | Screenshot |
| --- | ---: | ---: |
| Total traded volume | 385,669,169 | 385,669,169 |
| Closing price, rial | 6,730 | 6,730 |
| Net individual volume / total volume | 82.0335187% | 82% |
| Per-buyer volume / per-seller volume | 34.5417375 | 34.54 |
| Individual buy value / buyers, billion rial | 7.58163654 | 7.582 B rial |

Source fields: individual buy volume 342,469,169; individual sell volume 26,091,179; individual buyers 304; individual sellers 800. Net volume is 316,377,990. Stored actual net individual value is 2,129,223,872,700 rials = **212.92238727 billion toman** = **0.21292238727 trillion toman**.

These exact rounded matches support the screenshot's current-day metrics. Inference: its approximately +82 final chart bar appears to be the net-volume percentage, whereas our existing cash-flow bars show actual net value in trillion toman. Their heights are not directly comparable. No tooltip, historical point export or documented chart formula was available, so a full historical Mofid chart match has not been established. Existing charts/calculations remain unchanged.

## Five live Mofid spot checks — 2026-11-16 / 1405/08/25

Used the user's signed-in EasyTrader session, selecting five instruments randomly without replacement from the supported instruments visible in the Mofid watchlist: آوند, اطلس, آرام, توان, سیمانو. This particular sample consists of funds (two TSE, three IFB), not a representative sample of every equity or historical date. No orders or account settings were changed.

Compared the matching 1405/08/25 active SQLite records with Mofid's instrument detail panels, and fetched fresh dated TSETMC ClientType responses independently. All five stored individual purchase/sale values, volumes and investor counts matched the fresh official records. Mofid's total volume and exact turnover matched our records; individual/institutional counts and volumes matched to its displayed precision. Closing prices matched the visible Mofid prices.

| Instrument | Volume | Closing, rial | Our actual net, billion rial | Mofid displayed net, billion rial |
| --- | ---: | ---: | ---: | ---: |
| آرام | 2,580,605 | 53,402 | -12.372115794 | -12.419 |
| آوند | 675,585,438 | 31,900 | 196.120086322 | 196.145 |
| اطلس | 10,386,405 | 195,762 | 750.363204144 | 749.357 |
| توان | 85,575,113 | 91,614 | -15.102161867 | -13.633 |
| سیمانو | 13,781,232 | 51,934 | -556.655402748 | -557.041 |

**Metric distinction established by the sample:** all five Mofid displayed flow figures reproduce `(individual buy volume - individual sell volume) × displayed closing price`, scaled to billions of rials and rounded away from zero to three decimals. This is an inference from the five observed results, not inspected Mofid source code or a contractual API definition. Our flow remains actual `buy_I_Value - sell_I_Value`; changing it to force numerical agreement would replace actual transaction values with a closing-price estimate. توان illustrates the distinction clearly: actual −15.102161867 billion rials versus Mofid −13.633 billion rials. Different prices across executed buys and sells can produce this difference.

Derived net-volume percentages, buying-power ratios and per-buyer closing-price estimates were also consistent with the displayed figures and rounding. The earlier Avand per-buyer apparent difference (2.792 B versus computed 2.791146833 B) is explained by rounding away from zero, not a different buyer count.

A supplementary شتران check on the same date showed matching ClientType volumes/counts and a matching closing-price flow proxy. Its Mofid header volume (1,319,486,591) differed from both Mofid's detailed investor-volume total and its supplementary information volume (1,263,475,888), which matched our dated feed. The broader header discrepancy has not been explained; do not claim every displayed Mofid volume is identical. The five randomly selected fund totals did not show this discrepancy.

[Machine-readable results](mofid-spot-check-1405-08-25.json) retain only public market figures, with no personal account/order details. The checks do not establish a full historical chart match or certify all records.

The deployed `tse-daily.timer` was enabled and its most recent 20:30 Tehran execution succeeded (service result success, exit 0). Installed calendar entries are 20:30, 22:30 and 08:00 Asia/Tehran, with Persistent=true. The collector rechecks recent dates and unresolved dates; it does not manufacture Thursday/Friday sessions. No collection code or app behavior was changed during this verification.
