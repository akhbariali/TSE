# Ownership research snapshot implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement task-by-task after user approval. Steps use checkboxes for tracking.

**Status: awaiting user approval; none of these implementation steps has been executed.**

**Goal:** Generate a reproducible, source-traceable ownership-transfer and trading-concentration report from `KH - 14050819.xlsx`, with matching views in the existing no-login webapp, without claiming predictive power.

**Architecture:** Extend the existing standard-library modular monolith. A narrow adapter reads exact existing parser outputs; pure Decimal functions calculate four metric families; deterministic JSON/CSV/Markdown artifacts explain results and coverage. Existing SQLite serving views and the no-login application keep their current responsibilities.

**Tech stack:** Python 3.10+, Decimal, dataclasses, hashlib, json, csv, unittest. No external runtime dependency.

**Spec:** [Proposed architecture](../specs/2026-11-11-iran-market-research-design.md).

## Global constraints

- Python 3.10+; the first milestone adds no external runtime dependency.
- Preserve raw bytes and source text; Excel, local databases, downloaded evidence and generated reports remain ignored by Git.
- Financial core calculations use Decimal from exact source amounts; missing/invalid inputs produce null with a reason, never invented zero.
- Every metric declares its unit, formula version, scope, denominator, eligibility mask, exclusions and provenance.
- Unknown instrument identity/classification stays explicit; suffixes are never merged by heuristic.
- Unverified publication timezone or historical versions restrict data to descriptive use; no executable predictive/backtest claims.
- Keep the current no-login app working; no unrelated rewrite; reuse the existing UI design for the first milestone snapshot views.
- Source warnings do not discard independently checked fields; incomplete-table sums are not full-market totals.
- Numerical output is computed by tested code; an LLM may explain evidence but never supply financial numbers.

## File and interface map

| File | Responsibility |
|---|---|
| `tse_research/__init__.py` | Package version only |
| `tse_research/contracts.py` | Frozen exact observations, snapshot and result contracts |
| `tse_research/ingestion.py` | Adapter to existing `analyze_reports.analyze`; preserve source fields and quality |
| `tse_research/metrics/ownership.py` | Transfer, residual, bounded intensity, breadth and cancellation |
| `tse_research/metrics/concentration.py` | Trading-value HHI, effective instrument count and top-k share |
| `tse_research/snapshot.py` | Explicit single-workbook orchestration, eligibility and deterministic rankings |
| `tse_research/reporting.py` | Artifact schema, serialization, explanatory Markdown and manifest |
| `tse_research/__main__.py` | CLI arguments and controlled exit codes |
| `tests/test_research_ingestion.py` | Schema variations, exactness, measure-independent validity |
| `tests/test_research_metrics.py` | Independent arithmetic fixtures and boundary cases |
| `tests/test_research_snapshot.py` | Population gates, deterministic rankings and integration |
| `tests/test_research_reporting.py` | Reproducibility, traceability and safe failure |
| `app.py` and `web/static/{index.html,app.js,style.css}` | Thin snapshot routes and existing-app research view |
| `tests/test_research_web.py` | API scope, safe artifact resolution, states and downloads |
| `README.md` | Approved usage and interpretation |

No future enrichment/backtesting subsystem is scaffolded in this milestone.

### Contract decisions

`Observation(symbol, company, value_amounts, value_valid, volume_valid, source_data)` retains raw exact labels. `value_amounts` maps the four existing parser keys to `Decimal | None`. `Snapshot(date, source_hash, observations, source_daily, issues, metadata)` retains parser quality and source summary. Metadata includes supplied catalog report/attachment IDs, raw publication text with timezone confidence, parser version, Python/Decimal precision and source file basename; absent metadata is explicitly null.

`Metric(value, unit, denominator, eligible_count, excluded_count, reason, formula_version)` uses Decimal or integer values; a null value requires a reason. Pure functions receive observations or Decimal sequences, never file/network/database handles. Calculation context uses Decimal precision 50 with ROUND_HALF_EVEN; exact integer amounts are never rounded. Nonterminating ratios are recorded with that precision, and display rounding is separately declared. Raw input precision beyond this contract is rejected or explicitly raises precision before calculation, never silently truncated.

`load_snapshot(path: Path, metadata: dict | None = None) -> Snapshot`; `transfer(row) -> dict[str, Metric]`; `breadth(rows) -> dict[str, Metric]`; `cancellation(rows) -> Metric`; `concentration(turnovers, k: int = 10) -> dict[str, Metric]`; `build_report(snapshot: Snapshot) -> dict`; `write_report(report: dict, output: Path) -> list[Path]`.

A single explicit workbook is selected: no automatic revision selection or multi-date joining. Hash deduplication and dated revision resolution precede any future multi-workbook API. Current latest/best SQLite views are never used as a point-in-time history.

## Task 1: Exact observation adapter

**Files:** Create `tse_research/__init__.py`, `contracts.py`, `ingestion.py`, `tests/test_research_ingestion.py`.

**Consumes:** Existing `scripts/analyze_reports.py:analyze(path)` returning daily, records, issues; `source_data.value_amounts`, source rows/sheets and independent validity flags. Use a narrow import bridge to the existing scripts directory, matching repository import conventions; do not copy parsing logic.

**Produces:** `load_snapshot` and the contracts above. Source IDs/URLs are optional supplied metadata, not inferred from the basename. Hash bytes before and after parsing; fail if they changed during the read. Do not calculate from REAL SQLite fields or pre-rounded strings.

- [ ] Write a failing test using existing synthetic XLSX helpers: reversed investor headings map correctly; moved columns retain amounts; missing company is optional; missing sell value leaves that value null, while checked volume survives. Test an amount `9007199254740993` remains exact.

```python
self.assertEqual(snapshot.observations[0].value_amounts['retail_buy'],
                 Decimal('9007199254740993'))
self.assertIsNone(missing.value_amounts['retail_sell'])
self.assertTrue(missing.volume_valid)
self.assertFalse(missing.value_valid)
```

- [ ] Run `python3 -m unittest discover -s tests -p 'test_research_ingestion.py' -v`; confirm failure due to missing adapter, not a malformed fixture.
- [ ] Implement the frozen contracts and adapter. Map existing quality without upgrading warnings into invalidity or treating partial-table totals as complete. Reject negative/nonfinite required financial amounts even if a parser flag is accidentally permissive. Carry original fields and issue reasons.
- [ ] Run the targeted tests and existing workbook-layout tests. Test unsupported report family and source mutation produce a controlled failure.
- [ ] Review the exactness/provenance diff and commit adapter and tests only.

## Task 2: Transfer and counterflow calculations

**Files:** Create `tse_research/metrics/__init__.py`, `ownership.py`, `tests/test_research_metrics.py`.

**Consumes:** Observation contracts. **Produces:** `transfer`, `breadth`, `cancellation` signatures above.

Use buy-side turnover `T=RB+IB`, transfer `N=RB-RS`, institutional transfer `IB-IS`, residual `R=T-(RS+IS)`. Category nets sum to R. Preserve the parser's 1-rial row reconciliation tolerance; report every nonzero residual. Ratio `N/T` needs T>0 and |N|<=T; otherwise null with reason. No silent clamp. Aggregate intensity also checks the same bound and discloses aggregate residuals; it does not omit a row merely to manufacture a bounded total.

Breadth uses **nonzero eligible transfers** as denominator: `(n_positive-n_negative)/(n_positive+n_negative)`. Zero, missing and invalid counts are separate. This differs from breadth divided by all eligible rows, which is a separately named candidate in the catalog. Cancellation `1-abs(sum N)/sum abs(N)` needs positive gross transfer.

- [ ] Write failing tests with independent expected answers:

```python
# Two rows: (RB, IB, RS, IS)=(60,40,30,70),(120,180,130,170)
self.assertEqual(result['net_rial'].value, Decimal('20'))
self.assertEqual(result['intensity'].value, Decimal('.05'))
self.assertEqual(result['breadth'].value, Decimal('0'))
self.assertEqual(result['cancellation'].value, Decimal('.5'))
# Tiny tolerated row: (0,0,1,0): raw net -1, residual -1, intensity unavailable.
self.assertIsNone(tiny['intensity'].value)
self.assertEqual(tiny['net_rial'].value, Decimal('-1'))
```

- [ ] Run `python3 -m unittest discover -s tests -p 'test_research_metrics.py' -v`; confirm failure from missing functions.
- [ ] Implement the equations under the declared Decimal context. Required invalid fields suppress dependent calculations. Compute residual explicitly rather than substituting institutional=-retail.
- [ ] Add cases: all zero; one positive; one negative; mixed sign; exactly cancelling; missing; negative; ambiguous duplicate; tolerated imbalance with |N|>T; material imbalance; category swap; row permutation; positive unit scaling. A tolerated `(0,1,2,0)` has T=1, N=-2, R=-1: raw transfer survives, bounded intensity is null. For all-zero nets cancellation is null; all-zero signs breadth is null.
- [ ] Verify targeted tests. Review arithmetic and financial terminology; commit calculations and tests.

## Task 3: Trading-value concentration

**Files:** Create `metrics/concentration.py`; extend `tests/test_research_metrics.py`.

**Consumes:** Nonnegative finite eligible buy-side turnovers in a declared population. **Produces:** HHI, effective instrument count, top-k share, counts and denominator in Metric envelopes.

- [ ] Write failing expectations:

```python
r = concentration([Decimal(100), Decimal(300)], k=1)
self.assertEqual(r['hhi'].value, Decimal('.625'))
self.assertEqual(r['effective_count'].value, Decimal('1.6'))
self.assertEqual(r['top_k_share'].value, Decimal('.75'))
self.assertIsNone(concentration([Decimal(0)])['hhi'].value)
```

- [ ] Run the targeted suite; confirm the missing implementation fails.
- [ ] Implement `w_i=T_i/sum(T)`, `HHI=sum(w_i*w_i)`, `N_eff=1/HHI`, top-k descending sum. Require integer k>0. Empty/all-zero totals are null, negative/nonfinite inputs rejected. k>n uses n with the effective k disclosed. Exact zero-weight eligible instruments remain in coverage counts.
- [ ] Test equal weights (four instruments: .25,4), monopoly (1,1), a zero-weight row, permutation and positive scaling invariance, top-k monotonicity and declared precision. Check `1/n<=HHI<=1` for positive total within specified arithmetic precision. Do not use antitrust thresholds or label N_eff as investor count.
- [ ] Run the targeted suite and commit concentration and tests.

## Task 4: Coverage-aware snapshot and rankings

**Files:** Create `snapshot.py`, `tests/test_research_snapshot.py`.

**Consumes:** Snapshot and metric functions. **Produces:** `build_report` with schema version, definitions, metrics, rankings, coverage, provenance and caveats.

- [ ] Write failing integration tests: a complete synthetic two-row workbook produces the fixture values; the same rows in an incomplete source produce symbol results but null complete-market metrics with `incomplete_value_table`. Never pass a partial table as a full market.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_research_snapshot.py' -v`; inspect failure.
- [ ] Implement complete-table gate using existing quality evidence. Label universe **reported instruments, unclassified**, not all stocks. Show each metric's excluded rows, amount coverage where independently measurable, residual diagnostics, and source summary-versus-detail differences. Do not compare narrower equity percentages to mixed-instrument totals.
- [ ] Rank positive transfers descending, negative transfers ascending and turnover descending, ties by full normalized display symbol plus original symbol. Display absolute amounts beside ratios. Zero-turnover or invalid ratios remain null. No composite signal or buy/sell advice.
- [ ] Test equal-value ties, unknown instrument type, value-valid/volume-invalid, wrong headings, partial rows, footer conflicts, duplicate labels and negative amounts. Ensure all observations and exclusions trace to source row/sheet and raw hash.
- [ ] Run targeted tests, then `python3 -m unittest discover -s tests -v`; commit snapshot and tests.

## Task 5: Reproducible artifacts and CLI

**Files:** Create `reporting.py`, `__main__.py`, `tests/test_research_reporting.py`; update `README.md`.

**Consumes:** build_report output. **Produces:** JSON, instrument CSV, Markdown and manifest under ignored output directory.

- [ ] Write failing tests running the CLI twice on identical bytes with identical metadata and comparing artifact bytes/hashes. Assert exact Decimal strings in JSON/CSV, explicit null reasons, escaped Markdown symbol labels, and no wall-clock timestamp in analytical payload.

```python
self.assertEqual(first_json.read_bytes(), second_json.read_bytes())
self.assertEqual(first_manifest['payload_sha256'], second_manifest['payload_sha256'])
self.assertIn('not a return forecast', markdown_text)
```

- [ ] Run `python3 -m unittest discover -s tests -p 'test_research_reporting.py' -v`; confirm intended failure.
- [ ] Implement canonical UTF-8 sorted-key JSON with decimal-as-string, newline-terminated files, deterministic CSV order and stable Markdown formatting. Manifest hashes payload artifacts and records source hash, formula versions, parser version, parameters and numerical context. Separate optional wall-clock execution metadata so it cannot change deterministic artifacts. A manifest does not hash itself.
- [ ] CLI interface:

```bash
python3 -m tse_research snapshot \
  --workbook 'data/raw/KH - 14050819.xlsx' \
  --output reports/research/14050819
```

Optional `--metadata path.json` supplies catalog association; no network access. Exit 0 for a generated report including explicitly partial coverage, 2 for unsupported/malformed input or invalid arguments, and 1 for unexpected internal failure. Print actionable reasons without traceback for controlled input failures. Refuse to overwrite source workbooks; write artifacts via temporary files then replace.
- [ ] Test nonexistent/unsupported files, no writable output, deterministic ties, CSV escaping and malformed metadata. Generated output must never overwrite an input path. Document commands, units, source date versus publication, limited scope and metric interpretation.
- [ ] Run targeted and full tests; review the report language; commit reporting, CLI, tests and docs.

## Task 6: Existing-webapp snapshot views

**Files:** Modify `app.py`, `web/static/index.html`, `web/static/app.js`, `web/static/style.css`; create `tests/test_research_web.py`; update the existing surface brief only at implementation.

**Consumes:** Generated versioned artifacts from Task 5. **Produces:** Read-only `GET /api/research/snapshots`, `GET /api/research/snapshot?sha=<64 lowercase hex>` and `GET /api/research/export?sha=<hash>&format=json|csv|markdown`. Only generated valid manifests under fixed `reports/research/` are discoverable. For this first API, require exactly one active artifact per source hash: a fixed source-hash directory contains a single atomically replaced current manifest, which records payload hash, formula versions and parameters. Historical runs stay outside the discovery root. Duplicate/conflicting active manifests are rejected with a controlled conflict error; never choose by directory order. Downloads resolve the same manifest as detail and return its payload hash for consistency. Map hashes to trusted internal artifact paths; never accept caller filesystem paths. Recheck manifest/payload hashes and schema/version before serving, reject changed/incomplete artifacts and return controlled errors.

- [ ] Write failing API tests for list/detail/download, unknown hash (404), malformed hash/format (400), path traversal, tampered hash, malformed schema and stale/missing artifact. No formulas or float-derived aggregates are calculated in handlers. Preserve exact financial strings in responses; safe display strings can be added by reporting code.

```python
self.assertEqual(fetch('/api/research/snapshot?sha=' + '0'*64).status, 404)
self.assertEqual(fetch('/api/research/export?sha=../../etc/passwd').status, 400)
self.assertEqual(payload['metrics']['turnover']['value'], '596948215456567')
```

- [ ] Run `python3 -m unittest discover -s tests -p 'test_research_web.py' -v`; inspect expected missing-route failures.
- [ ] Implement artifact readers using fixed-root containment and schema/hash validation. Preserve existing CSP and file-download safety conventions. Return no artifact rather than recompute unreviewed data during a web request; no new write/sync endpoint is needed. List includes source hash, source date, report ID where present, quality/coverage and version, sorted deterministically.
- [ ] Add `#research` navigation and Research snapshot links to applicable report entries; pass selected source hash in route state. Sequence: source/date and original-file link, coverage/disclosures, four families with definitions/denominators, positive/negative contributors, concentration table, provenance and downloads. Snapshot selector lists generated snapshots; library reports without artifacts show “Research snapshot not generated” and the documented CLI command. This first slice starts with the actual sample and supports any explicitly generated compatible workbook, not an implicit claim that all 794 have new analytics.
- [ ] Follow the incumbent Operate/Read design in `DESIGN.md` and existing surface brief: blue shell, restrained white work areas, compact tables and source actions. Preserve archive/library/symbol explorer navigation. Keep nulls as “Unavailable” with reasons, never the current generic numeric formatter's default zero. Show unclassified reported instruments; never “all stocks.” Positive/negative text signs accompany color; expose exact source strings via accessible details rather than round-trip through JavaScript Number. Persian labels use isolated direction (`bdi`); keep dates unambiguous and amounts explicitly rial or visibly converted display units.
- [ ] Implement loading, not-generated, empty, partial, invalid-artifact and fetch-error/retry states. Use escaped source strings/textContent, table headers, associated selector labels, keyboard navigation, announced status and visible focus. Prevent stale async responses replacing a newer selected snapshot.
- [ ] Verify API tests and browser behavior with the sample, a partial synthetic report, all-zero report and a malicious source label. At desktop and 390px mobile, check reading order, scrolling tables, long Persian symbols, keyboard-only selection and downloads. Inspect rendered results; run the Impeccable mechanical detector once over changed UI targets after finishing. Add browser tooling only if already available; otherwise record manual checks without claiming automated browser coverage.
- [ ] Run the full Python suite, inspect console/network errors and commit the thin UI/API adapter and tests. No UI-specific financial formula is allowed.

## Task 7: Actual workbook acceptance and independent review

**Files:** Extend integration tests with opt-in local workbook checks; generated artifacts remain ignored. Add `docs/research/first-snapshot-verification.md` only after actual execution.

- [ ] Before running new calculations, independently recompute expected totals with a separate Decimal reduction over validated source fields (not the metric functions). Confirm sample SHA-256 `1ef908416e6103d35d563efa19b2edd5bbd372cee6bbe6e02d9ebcecffac6b8a`.
- [ ] Verify 1,192 retained instruments, turnover `596948215456567` rial, retail net `74101817413833` rial, and volume `52177504941` only under its independent completeness gate. Cross-check primary source total/footer cells, not only repeated output values. Record tolerated residuals and any unexplained differences before reporting new metrics.
- [ ] Run the CLI twice. Independently recompute HHI as `sum(T_i*T_i)/(sum T_i)^2`; compare against the metric result under the declared precision. Check cancellation against positive/negative transfer sums; inspect top-ranked source rows manually. Verify no auxiliary hidden/BI rows are counted twice.
- [ ] Run all tests and existing `python3 scripts/audit_reports.py`. Record actual counts, commands, source hashes, versions and limitations; never insert anticipated results into verification docs.
- [ ] Request independent financial/code review using Superpowers requesting-code-review. Supply the approved spec/plan, exact diff and verification evidence. Resolve material findings and rerun affected checks.
- [ ] Confirm `git diff --check`, raw Excel/data/reports ignored, and no unrelated changes. Commit the reviewed milestone. Publish/push only within the user's authorized repository workflow; do not merge or deploy automatically.

## Acceptance gate and next milestone

Acceptance requires all seven tasks, fresh tests, independent numerical checks, reproducible artifacts, transparent partial-data behavior and review. No predictive success is required or claimed. The next proposed milestone is trailing-only anomaly/persistence analysis with calendar, history and population gates; price enrichment/backtesting is a separate project after provenance and execution data are verified.
