# Methodology

How scores, gaps and priorities are calculated.

## 1. Scoring each subcategory
Every one of the 106 CSF 2.0 subcategories gets two scores on a 0–4 scale:

- **Current** — how the organisation operates *today*.
- **Target** — the realistic maturity it *should* reach, given its size and risk.

The 0–4 scale is adapted from the CSF Implementation Tiers:

| Score | Tier | Meaning |
|---|---|---|
| 0 | Not implemented | Doesn't exist, or unknown |
| 1 | Partial | Ad hoc, reactive, undocumented |
| 2 | Risk Informed | Aware; inconsistent practices |
| 3 | Repeatable | Documented, consistent, policy-backed |
| 4 | Adaptive | Measured and continuously improved |

## 2. Gap
```
gap = max(0, target − current)
```
Clamped at 0 so exceeding a target never shows as a negative gap.

## 3. Priority
A pure gap treats "2 → 4" the same as "0 → 2". But a subcategory sitting at
**0** is usually more urgent than one already at a decent level, because it means
the control is absent entirely. So priority weights the gap by how low the
current score is:

```
weight = gap + (4 − current) / 2

High    weight ≥ 3.5
Medium  2 ≤ weight < 3.5
Low     0 < weight < 2
—       gap = 0
```

This pushes **foundational, missing controls to the top** of the roadmap, which
is where a real remediation programme should start.

## 4. Function & category rollups
Function and category scores are simple averages of their subcategories'
Current/Target/Gap. "% to target" = current ÷ target. These drive the Dashboard
and the heatmap.

## 5. Roadmap
The roadmap is the subcategories with a gap > 0, sorted by `weight` (then by raw
gap), top 25. Each item carries Owner / Effort / Target-date columns to fill in —
turning the assessment into an actionable plan.

## 6. How to run a real assessment with this
1. Define scope (`docs/scope.md`): assets, data, suppliers, obligations, threats.
2. Gather evidence per subcategory (interviews, config reviews, existing docs).
   Record it in the Evidence column — evidence is what separates an assessment
   from a guess.
3. Score Current honestly against that evidence.
4. Set Target per subcategory to a realistic tier for the organisation.
5. Review the Dashboard and Roadmap; agree owners and dates.
6. Re-assess periodically and track movement.

## Limitations
- Maturity scoring is inherently judgement-based; two assessors may differ by a
  point. Consistency comes from recording evidence and applying the scale
  definitions the same way each time.
- A maturity assessment measures how well-managed controls are, **not** whether a
  specific system is technically exploitable. Pair it with technical testing for
  a full picture.
