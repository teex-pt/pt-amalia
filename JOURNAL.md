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

## Standing decisions

- Every dataset sample is gated by deterministic code verifiers; ground truth
  is computed by templates, never by a model.
- Teachers must be Apache 2.0 (never Claude/GPT outputs).
- Honesty/DPO negatives always come from AMALIA itself (on-policy).
- Acceptance rule for any checkpoint: pt-PT harness up, international
  benchmarks and controls within 1–2 points.
- Decontaminate against the consortium benchmarks (pt_exams, LegalBenchPT,
  alba, cultura_viva) before any dataset release.
