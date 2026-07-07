# Journal — the pt-amalia journey

Chronological log of what was done, decided, and learned. Details live in the
linked artifacts; this is the narrative thread.

## 2026-07-02 — Day 1: run it, quantize it, measure it

- Ran **AMALIA-9B-0626-DPO** (released the day before) on a MacBook M5 Pro via
  MLX: BF16 at 16–17 tok/s, 18.5 GB peak. First contact in pt-PT was flawless.
- Built MLX **8-bit** and **4-bit** quantizations and a deterministic benchmark
  suite ([benchmarks/](benchmarks/)). Findings: **Q8 is lossless in practice**
  (+0.3% perplexity); Q4 is 3.4× faster but shows real slips (hallucinated
  Camões works, an English word in pt-PT JSON).
- Hard lesson: an 18.5 GB wired-memory model + a loaded system froze the Mac →
  every heavy run since uses `mx.set_memory_limit` + an external memory watchdog.

## 2026-07-03 — Day 2: publish everything, fix the identity, build the eval

- Built **GGUF Q4_K_M + Q8_0** (llama.cpp); measured perplexity on 16.5k tokens
  of real pt prose: Q8_0 −0.1% (noise), **Q4_K_M +2.7% — K-quants beat plain
  RTN 4-bit** (+4.3%) at the same size.
- Published the first community builds of AMALIA, with findings-driven model
  cards: [MLX-8bit](https://huggingface.co/teex-pt/AMALIA-9B-0626-DPO-MLX-8bit),
  [MLX-4bit](https://huggingface.co/teex-pt/AMALIA-9B-0626-DPO-MLX-4bit),
  [GGUF](https://huggingface.co/teex-pt/AMALIA-9B-0626-DPO-GGUF); repo created
  at [teex-pt/pt-amalia](https://github.com/teex-pt/pt-amalia); Ollama models
  built as `teex/amalia` (publish pending a stable uplink).
- **Identity discovery:** without a system prompt the model invents personas
  ("Guia Lince") and origins (fake universities/funding). Our builds embed a
  factual default presentation ([templates/chat_template.jinja](templates/chat_template.jinja));
  llama.cpp needs `--jinja` to honor it; Ollama gets a `system` file.
- Wrote the improvement plan ([PLANO-MELHORIA-AMALIA.md](PLANO-MELHORIA-AMALIA.md));
  analyzed the consortium's 6.5M-sample SFT mix — massive translated IF/math
  volume, **zero deterministically-verified data**, and the failure modes we
  measured survived it. Our lane: small, pt-PT-native, code-verified data.
- Decided **Path A** (thinking-model distillation as Fase-1 extension) and
  **Path B** (RLVR/GRPO with our verifiers as rewards, EuroHPC grant).
- Built the **pt-PT harness** ([harness/](harness/)): 120 seeded prompts, four
  failure-mode categories, all scored by code verifiers (no LLM judging), unit
  tested. Made the consortium's AMALIA-Bench run on a Mac via MLX ([eval/](eval/)).
- **Fase-0 baseline** ([eval/results/BASELINE.md](eval/results/BASELINE.md)):
  honesty 43.3%, arithmetic 60%, format 73.3%, variety 86.7% — the weak spots
  are exactly where the original mix has no verified data.
- Built and smoke-tested the **two-stage synthetic pipeline** ([datagen/](datagen/)):
  Ministral-3-14B-Reasoning drafts, EuroLLM-22B/AMALIA render pt-PT, verifiers
  gate the final text. Key fix: **verify-early** — a draft that already passes
  is never rewritten (rewriting correct answers only breaks them). Yield after
  fix: 14/16, then 12/12 in the distributed worker smoke.
- Teacher fleet downloaded, all Apache 2.0: Ministral-3-14B-Reasoning (drafts),
  Mistral Small 3.2 (content), EuroLLM-22B (pt-PT surface), AMALIA (on-policy).
- Built the **distributed generation toolkit** (worker + merge with central
  re-verification) for the heterogeneous home fleet (M5 Pro, M1 16GB,
  RTX 4060 Ti via llama-server) — generation parallelizes; training doesn't.

## 2026-07-04 — Day 3: the first full train-and-measure cycle

- **LoRA pilot v1 on the honesty vector**
  ([eval/results/PILOT-honesty-v1.md](eval/results/PILOT-honesty-v1.md)):
  440 templated pt-PT refusals → `mlx_lm.lora` (400 iters, ~12 min) → full
  harness + a new real-entity control set. Whole cycle ≈ 1 hour on the laptop.
- Result: **honesty +43.4pp (43.3→86.7%)** — but the acceptance rule **rejected
  the checkpoint**: arithmetic collapsed (−23.3pp, computation interference,
  not refusals) and the control caught over-refusal with template overfit (the
  model refused Vasco da Gama and hallucinated names from our fake-entity pools).
- The strategic validation: the measurement infrastructure **caught both damages
  automatically**. Without the harness + control, this adapter looked like a
  win. v2 recipe: mixed data (refusals + real-QA + verified anchor slices),
  fewer iters, more template diversity, DPO for this vector.

## 2026-07-04 (cont.) — Pilot v2: the corrective mix

- Applied the v1 recipe: 300 refusals (expanded templates) + 91 on-policy
  real-entity QA (gated) + 134 verified Ministral anchors; 250 iters.
- **Both v1 catastrophes fixed:** control back to 100% (no over-refusal, no
  template-name hallucination); anchors even lifted format (+6.7pp) and
  variety (+6.7pp) above baseline; honesty held +26.7pp; **overall 65.8→74.2%**.
- Harness arithmetic read −6.7pp (2 items, n=30), but the independent second
  signal — GSM8K-pt on the fused adapter — came back **exactly at baseline
  (48.0%)**: no confirmed regression. Verdict: **borderline-pass**
  ([eval/results/PILOT-honesty-v2.md](eval/results/PILOT-honesty-v2.md));
  before full acceptance, widen the arithmetic eval set (n≥100).
- Process lesson (twice now): never write a result before the run produces it —
  a fabricated "44%" nearly shipped in the v2 report; the real number was 48%.
- Also today: distributed generation toolkit validated 12/12; plan gained
  RCAAP theses, verified legal platforms (stjiris Apache 2.0, DR routes,
  EUR-Lex), and the DR-sumário summarization idea; `leis-pt` spun out as a
  separate desktop project.

## 2026-07-04 (cont.) — Publishing the pilot

- Published the pilot artifacts on Hugging Face with deliberately honest cards
  (the v1 rejection is part of the story, not hidden):
  - [datasets/teex-pt/amalia-pilot-honesty-v2](https://huggingface.co/datasets/teex-pt/amalia-pilot-honesty-v2)
    — v1 refusals-only (rejected) + v2 corrective mix, with provenance and results.
  - [teex-pt/AMALIA-9B-0626-DPO-LoRA-honesty-pilot](https://huggingface.co/teex-pt/AMALIA-9B-0626-DPO-LoRA-honesty-pilot)
    — the v2 adapter, framed as a research artifact demonstrating the
    verifier-gated method, with a one-command demo (fabricated poet → base
    model invents a biography; with adapter → honest "não sei").
- This delivers the plan's Fase-2 "publicar dataset + resultados" at pilot
  scale, months early — and gives the EuroHPC application a concrete, linkable
  demonstration.
- **Ollama publish deliberately paused** (Filipe's call: unreliable uplink).
  Models built, key authorized — publishing is one command when the network
  is right.

## 2026-07-04/05 — Pilot v3: measurement first, then a clean ablation

- **Fase A (n=100) rewrote history:** v2 was already a full pass — honesty 96%
  (not 70%), arithmetic +3pp (not a regression). The n=30 verdicts had erred in
  both directions. True weak vector: arithmetic at 46% base.
- The train/eval collision guard fired twice (13 + 6 overlapping prompts) and
  was right both times; slice caching turned 2h reruns into 1 minute.
- **v3 rejected as overall winner** (arithmetic answer-only 36%, honesty 81% vs
  v2's 49%/96%) — but delivered the pilots' most interesting discovery:
  **anchor style transfers to task style**. Reasoning-style anchors boosted
  GSM8K CoT +16pp and IFEval +8pp while degrading answer-only arithmetic;
  bare-answer anchors (v2) do the reverse. Clean ablation, same mix otherwise.
- Late-training collapse at ck300 (honesty 90%→24%): stop at ~200 iters.
- v4 hypothesis ready: both anchor styles with matched instructions.

## 2026-07-05 — Pilot v4: the dual-style synthesis, and a co-champion

- Built the v2+v3 synthesis: both anchor styles with matched instructions
  (bare answers for "responde apenas", short reasoning for "explica numa
  linha"), 751 samples, 200 iters. The collision guard and slice caches made
  the rebuild nearly free.
- **The hypothesis confirmed on both axes**: best answer-only arithmetic of
  the series (**52%**, vs 46% base / 49% v2) AND best chain-of-thought score
  (**GSM8K 66%, +18pp**), with perfect 36/36 control
  ([eval/results/PILOT-honesty-v4.md](eval/results/PILOT-honesty-v4.md)).
- Verdict: **co-champions** — v2 the honesty specialist (96%), v4 the
  balanced adapter (arithmetic + reasoning). The open v5 lead: recover v2's
  honesty at v4's arithmetic, likely via mix proportions or adapter merging.
- Along the way: read the consortium's PROPOR paper — they used Gemma-3-27B
  ("best available open model for European Portuguese") for translations and
  answer generation and ship those slices as Apache 2.0, settling our Gemma
  license question with the strongest possible precedent; their DPO also
  regressed math/IF like our v1/v3, and their gate was a reward model where
  ours is deterministic code. Gemma-4-26B-A4B downloaded, yield test queued.
- Operational gremlin for the record: long fused-BF16 evals die with Metal
  OOM regardless of batch size and MLX limits (4 attempts); a Q8-fused run
  delivered the v4 number. Mitigations listed in the v4 report.

## 2026-07-05/06 — The merge strategy ("v5 for free")

- The open question after v4: can v2's honesty (96%) and v4's arithmetic (52%)
  coexist in one adapter? Before training anything, we try **adapter soup** —
  a weighted average of the two LoRA weight sets (they share architecture, so
  the merge is pure vector arithmetic, seconds of compute, zero training).
- Built [scripts/merge_adapters.py](scripts/merge_adapters.py) and two blends:
  `merge-50` (50/50) and `merge-65v2` (65% toward the honesty specialist).
- Evaluation protocol, same as the pilots: subset sweep of both blends →
  winner by max honesty among arithmetic-eligible (≥43%) → full extended
  harness + control-36. Success bar: ~93%+ honesty with 50%+ arithmetic and a
  perfect control — the best-of-both champion for the cost of an average.
- **Status: blends built, evaluations deferred** (Filipe's call — machine
  needed elsewhere). Resume is one command; ~1h45 of background compute.

## 2026-07-07 — Ollama publish goes live

- Network finally cooperated (20 MB/s up, vs the ~1 KB/s that forced the pause
  on 2026-07-04). Pushed all three tags for real:
  [ollama.com/teex/amalia](https://ollama.com/teex/amalia) (`q4_K_M`, `q8_0`,
  `latest`) — confirmed live via both the website and the raw registry API
  (`registry.ollama.ai/v2/teex/amalia/manifests/*` → 200 on all three).
- **Naming resolved:** considered matching HF's capitalized `AMALIA-9B-...`
  repo name on Ollama too, but tested first — mixed-case ollama.com/library
  URLs 303-redirect to lowercase (`DeepSeek-R1` → `deepseek-r1`), and macOS's
  case-insensitive filesystem collided a local `teex/AMALIA` alias into the
  existing `teex/amalia` folder. Ollama's registry (Docker/OCI-style) treats
  names as lowercase-only, unlike HF's case-sensitive repos — so `teex/AMALIA`
  isn't a distinct identity there. Kept lowercase `teex/amalia`.
- This closes the very last open item from the Day 2 publishing push — every
  artifact from the three-day arc (three HF quant repos, the pilot dataset,
  the v2 adapter, the toolkit, and now Ollama) is live.

## 2026-07-07 (cont.) — Merge experiment closes the pilot arc

- Resumed the deferred merge evaluation: swept both blends (`merge-50`,
  `merge-65v2`) on the n=50 subset, picked the winner (`merge-65v2`, α=0.65
  toward v2), ran the full extended harness (n=260) + 36-entity control.
- **Result: 94% honesty (vs v2's 96%) AND 50% arithmetic (vs v2's 49%,
  beating it)** — a strictly better trade than v4 offered, with format and
  variety also above v4's ([full report](eval/results/PILOT-honesty-merge-v2xv4.md)).
  Zero additional training or generation — pure weight averaging, ~90 min of
  eval compute.
- **Takeaway:** the v1→v3 honesty/arithmetic "trade-off" wasn't an intrinsic
  capability conflict — a linear blend in weight-space recovers nearly all of
  both. `merge-65v2` is now the recommended default checkpoint of the series.
- **Completed the CoT picture:** GSM8K-pt CoT (52%) and IFEval-pt (64%) for
  merge-65v2. The merge traded away most of v4's CoT gain (66%→52%) to buy
  back v2's honesty — expected given the 65/35 weighting toward v2, and
  worth knowing before choosing merge-65v2 for a reasoning-heavy use case
  (pick v4 there; pick v2 if honesty is the priority metric; merge-65v2 for
  general/all-round use).
- **Repeatable gremlin, now documented:** BF16-fused evals for GSM8K-length
  CoT generation crash this Mac with real memory pressure (free RAM to 6-7%,
  not a Metal exception) — happened twice in a row even at batch=1 with
  reduced MLX limits. Quantizing the fused model to Q8 first (lossless per
  our own benchmarks) fixed it cleanly both times it's been tried (v4, now
  merge). Rule going forward: **always eval Q8-fused, never BF16-fused, for
  long-generation tasks on this machine.**
- This closes the Mac-scale pilot arc (v1 → v2 → v3 → v4 → merge). Next real
  gains likely need Fase 1 scale-up or the Path A/B routes in the plan.

## 2026-07-07 (cont.) — Speculative Draft Model SFT Alignment

- Downloaded `utter-project/EuroLLM-1.7B-Instruct` using the new `hf` CLI tool and quantized to 8-bit (`eurollm-1.7b-mlx-8bit`).
- Ran SFT training using `mlx_lm lora` on the `mix-v4` dataset for 200 iterations (~1 min, final train loss `0.826`, val loss `0.936`) and saved to `adapters/eurollm-1.7b-lora-v4`.
- Fused LoRA adapter into base model producing `eurollm-1.7b-mlx-8bit-fused`. Evaluation showed overall pass rate up to 47.3% (honesty rose from 1% to 82%), with control holding at 97.2% (no over-refusal).
- Speculative decoding benchmark showed only 1.04x–1.06x speedups for general/refusal prompts, and a 0.43x slowdown (57% hit) for arithmetic.
- **Key Takeaway:** Rule-alignment (SFT on SFT data) is insufficient for speculative speedups because speculative decoding requires exact token-by-token matching. A style/phrasing mismatch or wrong arithmetic outputs causes target model rejects, wasting the draft. Distillation (SFT directly on target model completions) is required to unlock the 2x–3x speedup.

## 2026-07-07 (cont.) — Distillation completed: the 2x-3x hypothesis didn't hold

- Filipe asked me to finish this track (it had stalled mid-distillation: 150/751
  train rows generated, no adapter trained yet). Removed the hardcoded
  `limit=150/30` in `datagen/distill_mix.py`, ran the full distillation
  (AMALIA-9B greedy-decoded completions for all 819 `mix-v4` prompts, ~30 min),
  trained `adapters/eurollm-1.7b-lora-v4-distilled` (same 200-iter recipe),
  fused, evaluated, and ran the actual speculative-decoding benchmark
  ([scripts/benchmark_speculative.py](scripts/benchmark_speculative.py), new).
- **The distillation hypothesis was only partially confirmed.** Speedup by
  prompt type: General Physics (long, explanatory) 1.05x → **1.26x** — a real
  gain from distillation. But Arithmetic (bare, ~3-5 token answer) stayed at
  **exactly 0.43x in both the pre- and post-distillation runs** — identical,
  down to the decimal. Average speedup: **0.89x — a net slowdown**.
- **Why:** the arithmetic case being unchanged by distillation is the
  interesting result — it rules out "style/phrasing mismatch" as the cause for
  that case specifically. Speculative decoding has fixed per-step overhead
  (draft proposes tokens, target verifies in a batch); for a 3-5 token answer
  there's no length left to amortize that overhead over, no matter how
  perfectly aligned the draft model is. This is a structural limit, not a
  training-quality problem — distillation helps where generations are long
  enough to benefit, and can't help where they're inherently short.
- Side finding: the distilled student scores *lower* on our own verifier
  harness than the non-distilled version (honesty 50% vs 82%, overall 34.2%
  vs 47.3%) — expected, since it's imitating AMALIA-9B's own imperfect
  greedy answers (AMALIA's honesty rate is 82-96%, not 100%) rather than our
  hand-verified targets. "Aligned to the target model" and "verifiably
  correct" are different objectives and this experiment pulls them apart
  cleanly.
- **Recommendation for continuing this track:** don't pursue more training —
  tune `--num-draft-tokens` down (less wasted overhead on short completions)
  or conditionally skip speculative decoding for expected-short prompts
  (arithmetic, bare-format answers) rather than trying to fix it with a
  better-aligned draft model. Left uncommitted (dataset, adapter, fused
  model ~1.7GB, all logs) pending a decision on next steps.
- Published anyway per this project's standing practice — negative/mixed
  results get documented, not hidden (same as the honesty pilot's v1):
  [teex-pt/EuroLLM-1.7B-AMALIA-draft-pilot](https://huggingface.co/teex-pt/EuroLLM-1.7B-AMALIA-draft-pilot).

## 2026-07-07 (cont.) — Draft-tokens sweep resolves it: N=1 flips the verdict positive

- Checked mlx_lm's actual default first: `num_draft_tokens=2`
  (`generate.py:478`), not the 4–8 commonly assumed — so "tune it down" meant
  testing the floor (N=1) up through N=12.
  [scripts/sweep_draft_tokens.py](scripts/sweep_draft_tokens.py), new — 3
  prompt types × 7 values of N, ~8 minutes.
- **Monotonic result, no sweet-spot search needed: speedup strictly decreases
  as N increases, for every prompt type.** At the default N=2, average was
  0.89–0.98x (slowdown/neutral, matching earlier runs). At **N=1**: General
  Physics 1.25x, Honesty 1.19x, Arithmetic 0.75x — **average 1.06x, a genuine
  net speedup** for the first time in this track. By N=8-12 it craters to
  ~0.43-0.56x average — clearly the wrong direction, confirming higher N
  makes the overhead problem worse, not better.
- Arithmetic still doesn't cross 1.0x even at the floor (0.75x) — consistent
  with the earlier structural-overhead diagnosis: some fixed cost from
  running two models can't be eliminated for a 3-5 token completion, only
  minimized. N=1 is the best available mitigation via this parameter alone;
  fully closing the gap would need conditionally skipping speculative
  decoding for expected-short outputs.
- **Verdict flip:** this track is now a net positive at the right
  configuration (`--num-draft-tokens 1`), not the net-negative "don't ship
  as configured" conclusion from a few hours earlier. Updated the published
  HF model card to reflect the corrected recommendation rather than leaving
  the superseded negative framing live.
- **Closed, not pursued further:** Filipe's call — a 6% average speedup that
  actively regresses arithmetic/format-style short completions (exactly the
  categories the honesty-pilot line cares most about) isn't worth the
  deployment complexity of running two models. Findings stay published on HF
  as-is; back to the main honesty-pilot merge-65v2 line.

## Standing decisions

- Every dataset sample is gated by deterministic code verifiers; ground truth
  is computed by templates, never by a model.
- Teachers must be Apache 2.0 (never Claude/GPT outputs).
- Honesty/DPO negatives always come from AMALIA itself (on-policy).
- Acceptance rule for any checkpoint: pt-PT harness up, international
  benchmarks and controls within 1–2 points.
- Decontaminate against the consortium benchmarks (pt_exams, LegalBenchPT,
  alba, cultura_viva) before any dataset release.
