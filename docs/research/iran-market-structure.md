# Iranian market structure and enrichment constraints

Research date: **2026-11-11**. Research only; no application changes. Exact accessed sources and access failures are in [sources-market-structure.md](sources-market-structure.md). Labels below distinguish official-host observations from binding rules. A working endpoint does not establish an API contract, redistribution permission, complete history, or point-in-time availability.

## Findings that affect this archive

1. **A workbook symbol is insufficient as a permanent security identifier.** Preserve its original text and suffix, normalize Persian/Arabic letters only for matching, and resolve against a dated instrument master. Do not collapse ordinary shares, rights, funds, bonds, options, block-market symbols, or renamed instruments into one company series. The archive's mixed detailed tables must not be labeled an equity-only universe.
2. **Neither a fixed price limit nor a fixed base-volume rule is defensible across the archive.** A verified official-host snapshot for فولاد, dated `20261111`, reports `baseVol: 1` and price thresholds 4,670–4,950; the threshold endpoint also returns a prior-day row. This is evidence about one observed instrument/session, not a nationwide rule or historical base volume. [M4–M6]
3. **Closing price, last trade, and investor-category purchase VWAP answer different questions.** The archive can calculate a checked investor-category execution VWAP from its own volume/value pair. It cannot infer a closing return, high/low, or total return from that value. Official daily data expose separate closing and trade-price fields. [M5, M9]
4. **Participant counts require enrichment and semantic validation.** A live official-host client-type endpoint exposes category counts and quantities, but no explicit session date in its response. The attempted historical endpoint failed. A community README calls the counts “تعداد معاملات” (number of trades), illustrating why wrapper labels cannot settle whether counts mean distinct trading codes, persons, accounts, or executions. Until an authoritative definition and dated history are verified, label these as *source-reported client-category counts*, not unique investors. [M7, M9]
5. **Publication time is the information cutoff.** CODAL exposes both sent and published timestamps, reporting-period titles, corrections, and original document links. A financial period end or company event date is not its public availability date. Store each publication/correction separately and retain the version available at the research signal cutoff. [M8]

## Venues, boards and instruments

The official IFB navigation separately lists first, second, نوآفرین, پایه and توافقی markets; its base-market page separately lists yellow/orange/red boards. It also exposes derivatives, Islamic securities, fund categories and mortgage-priority rights. TSE and IFB are distinct venues under the SEO regulatory framework, rather than interchangeable names for a single equity universe. [M1–M3]

In the verified فولاد master response, `flowTitle` is `بازار بورس`, `cgrValCotTitle` is `بازار اول (تابلوی اصلی) بورس`, and industry is `فلزات اساسي`. Those labels establish the sample classification. They do not establish a universal mapping of every numeric code. Obtain all venue/board/type dictionaries before filtering an expanded universe. IFB's base-market descriptive text mentions both normal bounded and negotiated unbounded transactions; the page is undated and may retain older terminology, so use it as an official description, not a current trading-rule specification. [M2, M4]

A market-watch request with a seemingly restrictive `paperTypes[0]=1` still returned bonds and multiple `flow` values. Query parameters alone therefore do not certify a clean common-equity population; inspect returned instrument classifications and exclusions. [M10]

## Price formation, halts and executable signals

The analytical distinctions below are requirements for future research, **not a verified current exchange rulebook**:

| Mechanism | Why a daily ownership signal can mislead | Evidence needed before executable backtesting |
|---|---|---|
| Continuous trading versus call auction | An opening/reopening auction can produce a discrete price and distinct order-entry/execution phases; a daily signal cannot assume execution at the displayed price | Dated phase schedule, auction rules, session/state records, actual prints |
| Daily upper/lower price bounds | A price at the ceiling/floor can restrict price discovery; rounded ticks mean an observed threshold ratio need not equal the headline percentage | Instrument/session thresholds, reference price, tick size and exceptions |
| Buy/sell queues | Unmatched displayed interest is not executed volume or money entering the market; a buy queue can prevent a buyer receiving a fill | Timed order-book snapshots, side/level interpretation, cancellations, executions and conservative fill assumptions |
| Base volume and closing-price calculation | Where a base-volume mechanism applies, the official close can differ from the last trade or ordinary value/volume VWAP | Historical base volume, applicable dated formula, prices and transaction classifications |
| Halts, suspensions and reopenings | Missing observations may reflect a halt, suspension, delisting, source failure or no trades; calendar-day forward-fill hides unavailable execution | Status transitions plus supervisor announcements and venue calendar |
| Block/negotiated and special transactions | Distinct transaction populations can distort turnover, participant categories and prices | Trading-channel/type identifiers and documented inclusion rules for each source |

**Verified operational evidence:** TSETMC's dated daily-price endpoint returned `dEven=20261111`, `hEven=122957`, `pClosing=4950`, `pDrCotVal=4950`, `priceFirst=4950`, `priceMin=priceMax=4950`, `qTotTran5J=1142422228`, `qTotCap=5654990028600`, and `zTotTran=9998`. The static-threshold endpoint returned that day's upper bound 4,950. Thus this sample traded entirely at its observed upper bound. It **does not prove an unfilled buy queue**: an order-book observation is still needed. [M5–M6]

The attempted instrument-state endpoint returned a nominal record with `dEven=0`, `insCode="0"`, `cEtaval="A "`, and null title. That response cannot substantiate a dated halt history or decode all state codes. Do not silently treat it as successful enrichment. The historical-price-list endpoint's newest record was `20261110` while the daily endpoint already exposed `20261111`; synchronization and source finality must be tested. [M11–M12]

**Unresolved official rules:** no operative, versioned text for current session schedules, queue priority, auction triggers, halt-duration thresholds, current cross-board price limits or base-volume formulas was extracted in this pass. IFB's legal index has a **public consultation draft** concerning dynamic base volume, a settlement decision dated `1396/11/04`, and versioned links to CMR. A draft is not enacted regulation; an old decision is not proof of the current settlement cycle. Linked IFB PDFs returned 404 and the CMR page yielded only its JavaScript shell. No current numeric limit, session time or settlement cycle is asserted here. [M3, M13]

## Fees, taxes and settlement

SEO's official fee landing page links **“سقف نرخ کارمزدها و خدمات در بازار سرمایه ایران (ویرایش 49)”**. The fetched PDF cover states last revision **1405/04/27**, previous revision **1403/04/24**; the web page was updated **1405/04/30 08:51**. Its cover explicitly says the bulletin is an informational compilation and the relevant Council/SEO board notifications govern. [M14]

As a **dated bulletin example**, its TSE table 1 for shares/rights lists aggregate buy `0.003712`, sell `0.0088`, and tax sell `0.005` with reference to direct-tax law article 143 bis. These correspond to 0.3712%, 0.88% and 0.5%; the sell aggregate already includes the listed tax. The table also contains component caps, a small-trade broker-fee provision, decision dates and historical effective-date footnotes. **These figures are not a verified universal current charge or a reusable constant for the full archive.** The revision changelog explicitly changes some discounts and market-maker/fund provisions. Fund units, debt, options, transaction channels and participant roles have separate tables. Confirm operative notifications, trade-date applicability, caps, discounts, tax law and participant exemptions before calculating net returns. The informational bulletin is much stronger evidence than an undated broker blog, but its own caveat matters.

Settlement affects usable cash and implementation costs even when daily returns are calculated correctly. The existence of a 1396 settlement-cycle resolution in the IFB index is verified; its content and current supersession were not. Do not hard-code `T+1`/`T+2` from this research. [M3]

## Instrument and field mapping

All numerical API fields below are observed names, not a complete officially published schema. Retain identifiers as strings, dates separately from capture timestamps, raw bytes and missing values. InsCode exceeds JavaScript's exact integer range; numeric coercion can corrupt it.

| Research concept | Source field / observed example | Constraint |
|---|---|---|
| TSETMC instrument identity | `insCode="46348559193224090"` | Stable source key candidate; historical aliases/security changes still require mapping |
| Source security identifiers | `cIsin="IRO1FOLD0009"`; `instrumentID="IRO1FOLD0001"` | Both exist and differ. Preserve both; do not equate or blindly call either the issuer ID |
| Symbol / issuer display | `lVal18AFC="فولاد"`; `lVal30="فولاد مباركه اصفهان"` | Display text is not a time-invariant identity |
| Venue, board, type, sector | `flow`, `flowTitle`, `cgrValCot`, `cgrValCotTitle`, `yVal`, `sector.cSecVal/lSecVal` | Need dictionaries, effective dates and historical memberships; today's sector/board can leak into past tests |
| Outstanding quantity / base volume | `zTitad=1935000000000`; `baseVol=1` | Current snapshot only; not historical float, free float, or a historical base-volume series |
| Unadjusted daily prices | `priceFirst`, `priceMin`, `priceMax`, `pClosing`, `pDrCotVal`, `priceYesterday` | Proposed meanings: first/min/max, official close, last trade, prior reference. Verify semantics and transaction coverage before use |
| Daily activity | `qTotTran5J`, `qTotCap`, `zTotTran` | Proposed volume, value, number of trades; reconcile price×quantity, units and exchange summary |
| Bounds | `psGelStaMin`, `psGelStaMax`, `dEven`, `hEven` | Multiple records may include the preceding session; select by date/time rather than first row |
| Client categories | `buy_I_Volume`, `buy_N_Volume`, `sell_I_Volume`, `sell_N_Volume`, `buy_CountI/N`, `sell_CountI/N` | I/N mapping to حقیقی/حقوقی is consistent with wrapper terminology but needs official schema confirmation; counts are not already in workbook flow data |
| Daily client sample | Buy quantities 897,812,127 and 244,610,101; counts 1,279 and 78 | Buy quantities sum to sample daily volume 1,142,422,228; same sell reconciliation. This supports coverage for the sample, not distinct-person semantics or a full history |
| Adjustment observations | `priceAdjust[].dEven/pClosing/pClosingNotAdjusted/corporateTypeCode` | Latest sample `20260803`, 2549 versus 2604; event type was null. A price discontinuity factor does not identify dividend versus capital action |
| Disclosure identity and availability | CODAL `TracingNo`, `LetterCode`, `Title`, `SentDateTime`, `PublishDateTime`, `Url`, attachment links | Link events to instruments through reviewed issuer mapping; retain original and amended publications |

A subtle wrapper naming risk: pytse-client's README describes `adj_close` as **قیمت پایانی** (closing price), while separately offering `adjust=True` for adjusted histories. Do not infer corporate-action adjustment from the attribute name alone. Its documented order-book capabilities are a research lead, not independently verified archival completeness. [M9]

## External-source adapter and gap map — research requirements only

| Enrichment | Candidate input and evidence | What the existing Excel archive lacks / acceptance requirement |
|---|---|---|
| Instrument master and dated universe | TSETMC InstrumentInfo; TSE/IFB official listing pages | Reviewed exact-symbol/suffix matching, both identifiers, type/venue/board, delisted/renamed aliases, dated coverage and rejected ambiguities |
| Returns and liquidity controls | Daily and historical TSETMC price endpoints | Raw OHLC/official close/last/volume/value/count; reconcile units and duplicates, handle source lag and unavailable sessions; validate common-equity subset |
| Participant-size or buyer/seller-power research | ClientType endpoint; wrapper history lead | Authoritatively defined and session-dated counts, tested history coverage, zero/null distinctions; independently validate amounts if multiplying average prices |
| Queue/limit/halt controls | StaticThreshold, market watch/order book, instrument state, supervisor messages | Session bounds, historical base volumes, valid status/phase codebook, timestamps, queue-side decoding; no executable-fill claim from daily bars |
| Corporate actions / return adjustments | TSETMC adjustment list plus CODAL AGM/dividend, capital increase, rights and correction notices | Event type, announcement/effective/ex dates, cash amounts, rights treatment and an explicitly chosen reinvestment convention; reconstruct raw and adjusted versions independently |
| Fundamentals and event studies | CODAL search and report attachments | Parse report periods and consolidation/audit/correction flags; retain first-publication availability and every superseding version |
| Trading costs and cash availability | SEO fee bulletin and operative notifications; dated settlement rules | Per-type, side, channel, role and date schedules, caps, tax/exemptions, execution and settlement conventions |

An adjusted price series is not automatically a total-return series. State whether dividends are reinvested, when cash is received, how rights/subscription cash and capital changes are treated, and whether factors were revised using later information. Preserve unadjusted prices and version the adjustment factors. Current EPS, P/E, NAV, float, market capitalization and board labels must not be substituted for historical values.

Before enriched, predictive or executable production analytics, the principal remaining source work is: obtain operative dated rules; validate identifier joins for a representative mixed-instrument sample; verify historical client counts and their definition; reconcile a small set of raw daily prices/adjustments with disclosures; and establish usable publication/market timestamps. Access successes above justify a controlled enrichment investigation, not a claim that those gaps have already been closed.
