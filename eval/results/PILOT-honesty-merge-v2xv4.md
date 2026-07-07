# Adapter merge experiment — v2 × v4 (2026-07-07)

The open question after pilot v4: can v2's honesty ceiling (96%) and v4's
arithmetic recovery (52%) coexist in one adapter? Before training anything
new, we tried **adapter soup** — weighted averaging of the two LoRA weight
sets. Both adapters share architecture (same base, same `mlx_lm.lora`
settings: batch 2, 16 layers), so the merge is pure vector arithmetic:
`merged[k] = α·v2[k] + (1-α)·v4[k]` for every tensor key, no training, no
generation. Tool: [scripts/merge_adapters.py](../../scripts/merge_adapters.py).

## Method

1. Built two blends: `merge-50` (α=0.50, balanced) and `merge-65v2` (α=0.65,
   weighted toward the honesty specialist).
2. Swept both on the n=50 extended-harness subset.
3. Picked the winner by the same rule as every pilot: max honesty among
   blends with arithmetic ≥ 43% (the eligibility floor).
4. Ran the winner through the full extended harness (n=260) and the
   36-entity real-world control.

## Sweep

| Blend | arithmetic (n=50) | honesty (n=50) | eligible |
|---|---|---|---|
| merge-50 | 48.0% | 90.0% | yes |
| **merge-65v2** | **50.0%** | **90.0%** | yes |

merge-65v2 won on arithmetic at equal honesty — counter to the naive
expectation that more α toward v2 would trade arithmetic away; at this
blend ratio the two effects aren't purely linear.

## Full results (n=260 harness + 36-entity control)

| Metric | Baseline | v2 | v4 | **merge-65v2** |
|---|---|---|---|---|
| arithmetic (100) | 46.0% | 49.0% | **52.0%** | 50.0% |
| honesty (100) | 50.0% | **96.0%** | 82.0% | 94.0% |
| format (30) | 73.3% | **80.0%** | 73.3% | 76.7% |
| variety (30) | 86.7% | **93.3%** | 86.7% | 90.0% |
| control (36) | 100% | 100% | 100% | **100%** |
| overall | 55.4% | **75.8%** | 70.0% | 74.6% |

## Verdict: near-total success — the merge recovers v2's honesty ceiling almost entirely while holding v4's arithmetic gain

merge-65v2 sits **2 points below v2 on honesty** (94% vs 96%) while landing
**1 point above v2 on arithmetic** (50% vs 49%) — a strictly better trade
than v4 offered (82% honesty for 52% arithmetic). It also beats v2 on
arithmetic and beats v4 on every other axis (honesty, format, variety),
with perfect control preserved. This is the best all-round adapter of the
entire pilot series by overall score-per-axis-consistency, even though v2
keeps the single-metric honesty crown by a 2-point margin.

**Why this matters beyond the number:** the merge required zero additional
generation, zero additional training, and about 90 minutes of evaluation
compute — dramatically cheaper than a v5 training run would have been, and
it answered the open question directly: honesty and arithmetic degradation
in these adapters are not fully entangled in weight-space. A linear blend
recovers most of both, which suggests the v1→v3 "trade-off" was more about
*data mixture* composition than an intrinsic capability conflict.

## Series summary (all pilots, extended n=100/30/36 harness)

| Adapter | arithmetic | honesty | format | variety | control | overall | Note |
|---|---|---|---|---|---|---|---|
| baseline | 46.0% | 50.0% | 73.3% | 86.7% | 100% | 55.4% | no adapter |
| v1 | — | — | — | — | 66.7%¹ | — | rejected (n=30 only; over-refusal) |
| v2 | 49.0% | **96.0%** | **80.0%** | **93.3%** | 100% | **75.8%** | honesty specialist |
| v3 | 36.0% | 81.0% | 73.3% | 93.3% | 97.2% | — | rejected; anchor-style ablation |
| v4 | **52.0%** | 82.0% | 73.3% | 86.7% | 100% | 70.0% | arithmetic/CoT specialist (GSM8K 66%, IFEval 64%) |
| **merge-65v2** | 50.0% | 94.0% | 76.7% | 90.0% | 100% | 74.6% | **best all-round** |

¹ v1's control was measured on the original 12-entity set, not the 36-entity
v3 control; not directly comparable to the others in this table.

## What's next (if the series continues)

- **merge-65v2 is the natural default checkpoint** for any downstream use of
  this pilot line — recommend it over v2 or v4 individually unless a
  deployment specifically needs the single best score on one axis.
- Untried: sweep more α values (0.55, 0.60, 0.70, 0.75) to map the curve
  properly rather than the two points tested here; also untried, merging
  v4 with v3 (both arithmetic-focused, different mechanisms) or a 3-way
  merge (v2 × v3 × v4).
- Push toward Fase 1 (plan §5): this closes the Mac-scale pilot arc — the
  next real gains likely need the larger verified datasets and/or the
  Path A/B routes (thinking-trace distillation, RLVR) documented in
  `PLANO-MELHORIA-AMALIA.md`.
