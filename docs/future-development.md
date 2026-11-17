# Future development notes

## Retail buying anomalies — initial implementation authorized 2026-11-16

The project's broader goal is to identify unusual individual-investor buying / ورود پول حقیقی. An anomaly need not mean unusually large trading volume or the largest absolute net inflow. Investigate persistent buying trends, changes in buying behavior, and unusual strength relative to the instrument's own historical baseline. These are future research directions, not implemented signals or proven predictions.

Initially deferred for credits on 2026-11-15. On 2026-11-16 the user authorized a narrowly scoped recommendations section, a reference check and the fund-checkbox alignment/English-label adjustment. Initial research rules now compare recent retail buying strength with each instrument’s own historical baseline. No existing chart was changed. Further threshold calibration and broader chart work remain future work.

### Mofid comparison reference: شتران

Saved EasyTrader screenshot (kept locally at `docs/references/mofid-shetran-1405-08-24.png`; excluded from Git because it includes account details), supplied by the user on 2026-11-15, for later comparison with our charts. Instrument: شتران (Tehran Oil Refining), TSETMC ID 51617145873056483. Screenshot session date: 1405/08/24.

The visible chart is labelled «روند معاملات حقیقی» and shows green/red bars across dates from roughly 1405/06/22 to 1405/08/24. The screenshot also shows «خالص خرید حقیقی» 82%, «قدرت خرید حقیقی» 34.54 and «سرانه خرید حقیقی» 7.582 B rial. These are reference observations only: the bar metric, units, calculation and sampling interval have not been verified. Do not assume it is the same series as our daily actual-value net retail flow. Later, compare matching dates, units and definitions before drawing conclusions or changing our calculation.

The current-day screenshot comparison is now recorded in [verification notes](tsetmc-verification.md#mofid-easytrader-reference-check--2026-11-16).
