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
