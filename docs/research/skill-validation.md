# Domain reference skill validation checkpoint

These are project-local reference drafts under `.agents/skills/`, not replacements for Superpowers workflows. They are committed for reuse/review. No measured behavioral improvement is claimed: a baseline agent already rejected most unsafe proposals. Its metric terminology left amount/quantity and concentration population ambiguous; the reference now specifies these contracts.

| Skill | Application case and observed result | Status |
|---|---|---|
| iran-market-research | Agent rejected blog popularity as alpha evidence, a single live API observation as universal law, and DOI metadata as read empirical findings. | Application checked |
| iran-market-data | Agent preserved symbol suffixes, blank versus zero, separate identifiers and unknown timezone; correctly called value/quantity execution VWAP rather than official close. | Application checked |
| financial-metric-design | Independent two-row arithmetic produced T=400,N=20,I=.05, HHI=.625, effective count1.6. Initial review found missing tolerance/partial/zero policies; reference revised and retested on (0,1,2,0), (0,0,1,0), partial and all-zero populations. Agent correctly retained raw transfer/residual and withheld invalid bounded intensity. | Application checked after revision |
| quantitative-validation | Agent rejected all-history selection followed by a relabeled holdout, random panel splitting, pre-publication outcomes and BH on selected tests. Proposed genuinely untouched future evaluation, date-grouped nested fitting, overlap controls and dependent-data uncertainty. Specific fold lengths and thresholds correctly remain experiment-design decisions. | Application checked |
| iran-market-backtesting | Reference written from existing baseline failures avoided and market-source research; independent application test not completed before user-requested pause. | Draft; validation pending |

Baseline used a generic startup skill but no domain references. Checks are qualitative retrieval/application cases, not controlled estimates of performance or exhaustive pressure testing. No unsupported RED-to-GREEN improvement claim is made. Temporary agent transcripts are local `/tmp` evidence and are not a durable committed test harness; this document preserves case/results and limits. Repeat scenarios when changing reference contracts. References do not authorize live trading or substitute for operative dated rules.
