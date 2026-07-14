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

## 2026-07-07 (cont.) — merge-75: mapping the α curve found a better champion

- First fixed a stale-publish gap: [teex-pt/AMALIA-9B-0626-DPO-LoRA-honesty-pilot](https://huggingface.co/teex-pt/AMALIA-9B-0626-DPO-LoRA-honesty-pilot)
  still shipped the original v2 adapter three days after merge-65v2 was
  proven the series champion — updated it, with an IFEval transcription
  error caught and fixed before publishing.
- Then mapped the merge's α curve properly: only two points (0.50, 0.65) had
  been tested. Built 4 more blends (0.55/0.60/0.70/0.75), swept all six.
  **α=0.75 wins on both arithmetic and honesty simultaneously** — no
  trade-off needed, the rare clean result.
- Full eval of merge-75: **dominates v2 on every axis** (matches honesty
  96.0%, format 80.0%, variety 93.3% exactly; beats arithmetic 51.0% vs
  49.0%; beats overall 76.5% vs 75.8%) while *also* tying v3's series-best
  IFEval (68.0%) and beating merge-65v2's GSM8K (54.0% vs 52.0%)
  ([full report](eval/results/PILOT-honesty-merge-v2xv4.md)).
- **merge-75 is the new recommended default checkpoint**, superseding
  merge-65v2 — republished to the same HF repo.
- Operational note: hit the recurring HF snapshot-incompleteness bug again
  (missing `.gitattributes`/`README.md`, now under a *new* commit hash for
  `amalia-llm/AMALIA-9B-0626-DPO` — the upstream repo was updated since our
  last check) and a watchdog false-positive (a pipeline's `sleep 15` between
  stages left a window with no matching process name, making the watchdog
  conclude prematurely that everything had ended while the script was still
  alive and about to start the next stage) — both diagnosed correctly rather
  than treated as real failures.

## Standing decisions

- Every dataset sample is gated by deterministic code verifiers; ground truth
  is computed by templates, never by a model.
- Teachers must be Apache 2.0 (never Claude/GPT outputs).
- Honesty/DPO negatives always come from AMALIA itself (on-policy).
- Acceptance rule for any checkpoint: pt-PT harness up, international
  benchmarks and controls within 1–2 points.
- Decontaminate against the consortium benchmarks (pt_exams, LegalBenchPT,
  alba, cultura_viva) before any dataset release.

## 2026-07-07 (cont.) — New direction: domain specialists, starting with K-12

- Discussed specializing rather than only fixing general behaviors — a K-12
  tutor and a Portuguese-law model are the two candidates. Both fit the
  project's core finding (small verified data beats generic volume) applied
  to topics instead of behaviors. Recommended K-12 first: lower stakes,
  faster validation loop, exam marking schemes give ground-truth-by-construction
  the same way our arithmetic anchors do. Legal is the bigger opportunity but
  needs a higher rigor bar (wrong legal info has real consequences) and has a
  natural feeder once `leis-pt` (the separate desktop project) has real data.
- **IAVE exam corpus collected**: verified `pt_exams`/PHEB's actual scope
  first (checked the PROPOR paper directly rather than trust the plan's
  vague caveat) — 2006-2023, six subjects only (Mathematics, Portuguese,
  History, Geography, Biology/Geology, Philosophy). IAVE actually publishes
  26 subjects across 3 sessions/year; used 2024-2025 to guarantee disjointness
  by year alone, so all subjects are usable, not just the 20 the benchmark
  never touches.
- Found IAVE's real archive (`?ano=YYYY` filter, not JS-hidden as the static
  homepage suggested) and confirmed live URLs for both years directly rather
  than guessing a filename pattern (filenames carry inconsistent manual
  suffixes — not programmatically predictable). 122 exam sittings, 244 PDFs
  (exam + marking scheme pairs), respectful rate-limited download —
  243/244 on the first pass, the one 404 was a transcription slip on my part
  (hyphen/underscore mismatch), fixed and confirmed 244/244.
  ([datagen/iave_registry.py](datagen/iave_registry.py),
  [datagen/iave_download.py](datagen/iave_download.py))
- Next: PDF text extraction into structured Q&A pairs (harder than the
  download — math notation, multi-column layout, pairing exam questions
  with their marking-scheme answers).
- Checked full K-12 scope while researching: what we built only covers
  **Ensino Secundário (12th grade)**. Portugal's K-12 has two more IAVE
  streams — 9th-grade finals (Provas Finais de Ciclo EB) and younger-grade
  diagnostics (Provas de Aferição EB, genuinely JS-rendered, harder to
  scrape) — both untouched. Real gap for a full K-12 tutor, deferred rather
  than blocking on it: the secondary corpus alone was worth validating first.

## 2026-07-07 (cont.) — IAVE extraction: 452 verified pairs, and a real bug caught

- `pdftotext -layout` confirmed the PDFs are true digital text (not scanned)
  — math notation still garbles under font-encoding quirks (confirmed by
  reading a derivative-rules formula sheet), but that's a font-mapping
  problem, not an OCR problem.
- Marking schemes use **three different answer-key formats** across subjects
  (a clean table for Filosofia; inline "item + dots + points" then a bare
  letter for Matemática A; inline then "Versão 1 – (X); Versão 2 – (Y)" for
  Física e Química A) — built pattern support for all three.
- **First pass: 78% pairing yield, Filosofia only 28%** despite being the
  cleanest test case. Root cause: marking-scheme tables zero-pad item
  numbers ("01.") but exam text doesn't ("1.") — fixed, Filosofia jumped to
  100%. A second bug (stray extra "." in some item-number lines) took
  Física e Química A from 0% to 100%. Yield: 94%.
- **Caught a real false positive during a spot-check**, not by luck —
  reviewing random samples turned up a Português item where the extracted
  "question" was open-response text but got labeled with a confident
  (D)/(C) answer. Root cause: exams are organized in groups (GRUPO I/II/III)
  with item numbering that *restarts per group*, so "item 4" can mean two
  different things in one exam, and the first (wrong) occurrence was being
  matched. Fixed with a safety gate (require 2+ lettered options in the
  matched text) plus scanning *all* occurrences of a reused number instead
  of stopping at the first — this is the "verify, don't assume" pattern
  from every pilot applied to a parsing pipeline instead of a training run.
  Final yield: **97%, 265 pairs**, expanded to **452 training samples**
  (both shuffled-option exam versions counted) after the false positive
  was fixed rather than just filtered out.
- Flagged (not hidden) the 25% of records from notation-heavy STEM subjects
  where math garbling is a known risk (`notation_risk` field) — plain-number
  items in those same subjects extract cleanly, so it's a coarse per-subject
  signal, not a per-item guarantee either way.
- Open-response items (richer content — grading rubrics with model-answer
  descriptors) intentionally out of v1 scope; different extraction problem
  ([datagen/iave/README.md](datagen/iave/README.md)).

## 2026-07-07 (cont.) — IAVE dataset published to HF, gated: a second real bug found while preparing the publish

- User asked whether to push the IAVE corpus to HF, "complementary to the
  one that already exists" (`amalia-pilot-honesty-v2`). Before assuming
  Apache-2.0 the way that dataset is licensed, checked precedent: that
  dataset is pure synthetic content (templates + on-policy + teacher
  drafts), this one is real IAVE exam text, a different situation.
  Checked how PHEB (LREC 2026, same source exams, same research team behind
  AMALIA-9B) handles this — they redistribute raw question text on a public
  GitHub repo with **no license file at all** and no IAVE attribution. Real
  precedent that this is treated as normal practice in this research
  community, but not the same as IAVE having granted redistribution rights.
- **Spot-checking a sample record before writing the card caught a second
  real bug**: PDF page footers ("Prova 501/1.ª F. • Página 12/ 15") plus
  next-page header text were bleeding into 90/265 (34%) of captured
  questions — `pdftotext -layout` linearizes pages back-to-back across the
  page break. Not caught by the aggregate 97% yield number, only by reading
  actual text. Fixed in `find_question_text()` (strip everything from
  `"Prova " + <3-digit exam code>` onward — verified that token never
  appears in legitimate question prose). **Yield rose 97% → 99%** (270/272
  paired, a few footer-inflated records had been failing the length cap),
  **462 clean training records** (416 train / 46 valid).
- The permission classifier blocked the initial publish attempt (a public
  HF dataset upload of content with unconfirmed redistribution rights,
  triggered by a question rather than an explicit go-ahead) — correctly:
  this was a genuine open call, not something to decide unilaterally.
  Presented the PHEB precedent and the license framing to the user directly
  and asked how they wanted to handle it (public / gated / hold off).
  Chose **gated (manual review)**: same content and card as a full public
  release, but HF's request-access flow adds a real accountability step
  before this specific text reaches someone, without blocking legitimate
  research use.
- Published: [teex-pt/amalia-iave-exams-2024-2025](https://huggingface.co/datasets/teex-pt/amalia-iave-exams-2024-2025)
  (`gated: manual`) — `extracted.jsonl`, `mix/{train,valid}.jsonl`,
  `extract-report.json`, and a card that documents scope, the two bugs
  found and fixed, `notation_risk`, and the license reasoning explicitly
  rather than a blanket Apache-2.0 claim over content we didn't write.

## 2026-07-07 (cont.) — K-12 eval design: no new evaluator class, but a held-out set was needed

- Asked whether running a LoRA pilot on the IAVE mix needs "a new class of
  evaluators." Ran a research→design→critique→synthesize workflow (7
  agents) against the actual harness code, the IAVE data, PHEB's own MCQ
  scoring methodology, and the project's standing plan/precedent, rather
  than answering from memory. Answer: **no** — `mcq` is a sixth category on
  the existing `harness/verifiers.py` pattern (`CHECKERS`/`MAX_TOKENS`
  dicts, dispatched by `item["category"]`), the same shape as `format`'s
  `starts_with` branch. PHEB's own `generate`-method scorer needs nothing
  more than regex-extract + exact match.
- **Real bug the investigation surfaced**: `iave_build_mix.py`'s
  train/valid split was row-level only — all 13 sittings then represented
  in `valid` also had train items from the *same* sitting, and 37 cases
  split a literal v1/v2 twin (same question stem, different correct
  letter) across both sides. Harmless for `valid.jsonl`'s actual job (SFT
  loss monitoring) but unusable as a held-out benchmark as-is.
- Implemented `check_mcq` using PHEB's 3-step cascade (boxed/paren →
  end-anchored letter → last bare letter). **Caught a real bug by testing
  it, not by trusting the design**: `re.IGNORECASE` on the bare-letter
  fallback matches the Portuguese word "a" (article/preposition), so a
  refusal like "não sei responder a isto" was misread as answering "(A)".
  PHEB's actual implementation is case-sensitive, not case-insensitive as
  the workflow's own critique had recommended — removed IGNORECASE
  entirely rather than shipping a plausible-sounding but wrong fix.
- Rewrote `iave_build_mix.py` to reserve whole exam sittings (not rows) for
  a new `harness/iave_prompts.jsonl` *before* the train/valid split —
  smallest sittings first, capped at one sitting per subject code, so no
  single large sitting (Economia A's F2 alone has 56 items) can dominate
  the holdout or gut that subject's training data. First attempt (random
  shuffle, no cap) drew 2 sittings that were 95% one subject; the
  deterministic smallest-first + one-per-code version gets 11 sittings, 37
  items, 11 distinct subjects. Registered the new file in
  `build_mix_v3.py`'s `load_eval_prompts()` so it's protected by the
  existing train/eval collision guard for *all* future mixes, not just
  this one. `mix/{train,valid}.jsonl` shrinks to 383/42 (425 total, down
  from 462) accordingly.
- Also found and fixed 60/270 records (22%) with a stray `\x07` (BEL)
  control character from a PDF bullet-glyph mapping failure — verified
  every occurrence sits between non-word characters before stripping it
  unconditionally, same discipline as the footer-bleed fix.
- Re-published the HF dataset with corrected counts and a new "Held-out
  evaluation slice" section disclosing the 37 reserved items even though
  they're intentionally not included in the published files.

## 2026-07-07 (cont.) — iave-v1 LoRA pilot: REJECTED, and why it matters

- Ran the full pilot: `mlx_lm.lora` on the 383-sample IAVE mix (200 iters,
  same recipe as honesty-v4 — rank 8, 16 layers, batch 2, lr 1e-5), then the
  full harness (ext + control36 + the new `mcq` set) on baseline vs. adapter.
  **Verdict: rejected.** `mcq` (the actual target) moved **0.0pp** (11/37 →
  11/37), while arithmetic (−4.0pp), format (−6.6pp), variety (−3.4pp), and
  control (−2.8pp) all regressed past the 1-2pp acceptance tolerance. Full
  writeup: [eval/results/PILOT-iave-v1.md](eval/results/PILOT-iave-v1.md).
- Verified the adapter was actually being applied before concluding
  anything (28/29 mcq responses changed text vs. baseline) — this was a
  real trained effect, not a load-path bug. The model clearly learned the
  output *format* (`"(X)"` exactly matching training targets) without
  learning to answer more items correctly.
- **Same failure mode as honesty-v1** (2026-07-04): single-vector SFT with
  zero diversity anchors. The IAVE mix is 100% MCQ, identical prompt
  template on every one of 383 samples — enough uniformity for a 9B model
  to latch onto "answer tersely with one bracketed letter" as a dominant
  pattern, which then leaked into arithmetic/format/variety, none of which
  want that style. honesty-v1→v2 already proved the fix (mix in anchors);
  this pilot didn't do that on purpose, to isolate whether the IAVE corpus
  alone moves the needle. It doesn't, at this scale.
- Promoting this to a standing pipeline rule rather than a one-off lesson:
  **never train a LoRA on a single homogeneous sample type** — always mix
  in anchors from other categories, even for a narrow specialization pilot.
- Cheap experiment (~10 min total train+eval), so the negative result cost
  little and taught a lot: reinforces the RAG-over-fine-tuning lean already
  reached independently while scoping leis-pt's objective #3 the same day.

## 2026-07-07 (cont.) — leis-pt F0: source-verification blocker found before writing any scraper

- Asked to launch leis-pt (Portuguese legal corpus project, spec-only until
  now) on the new `lw-lab1` SSH host (WSL2, RTX 4060ti) so it runs in
  parallel with pt-amalia work on the Mac. Set up key-based SSH access
  (`~/.ssh/lw-lab1`, `UseKeychain`, matching the existing `ubr-gcs`/
  `google_compute_engine` pattern) and confirmed CUDA is reachable from
  Python (`torch.cuda.is_available() == True`) even though `nvidia-smi`
  isn't on WSL's default PATH.
- Updated `leis-pt/PLANO.md` with three sequenced objectives (training
  corpus → vector search/MCP server SaaS → specialized model), reasoning
  from the iave-v1 result above: legal Q&A has higher hallucination stakes
  than exam MCQs, so a RAG-first model (calls the retrieval layer) is
  probably the right shape, not a parametric model that memorized the law.
- Before writing a scraper, verified the plan's two source claims directly
  rather than trusting the "✅ confirmado" notes in the spec:
  - `files.diariodarepublica.pt/1s/{year}/{month}/{issue}/{pages}.pdf` —
    **confirmed real and valuable**: found live example URLs, downloaded
    one, and its header already contains série/issue/date/órgão emissor/
    diploma title *and* the official `Sumário:` — meaning `amalia-sum-dre`
    needs no separate metadata source at all.
  - `diariodarepublica.pt/dr/legislacao-consolidada/` (the amendment-graph
    source, the plan's most-valuable-asset claim) — **blocked**: it's a
    fully client-rendered OutSystems React SPA (empty server HTML, `<div
    id="reactContainer">`). No JSON API found after checking robots.txt/
    sitemap, scanning the SPA's JS bundle, and searching dados.gov.pt/INCM
    open-data docs. The "✅ confirmado" in the original plan was almost
    certainly a human eyeballing it in a browser, not something a plain
    HTTP scraper can reach.
  - Left open for the user to pick: add headless-browser tooling to capture
    the SPA's real XHR calls, scope F0 down to the (working) PDF stream
    only, or try arquivo.pt's archive API as an indirect route.

## 2026-07-08 — iave-v2: anchor-mixing fix validated (mostly), matches honesty-v1→v2

- While the leis-pt consolidada crawl ran unattended on `lw-lab1` (see
  below), ran the fix `PILOT-iave-v1.md` prescribed: mix diversity anchors
  into the IAVE training data, replicating the honesty-v1→v2 correction
  exactly. New mix (`datagen/build_iave_v2_mix.py`): all 383 IAVE samples +
  250 randomly-sampled anchors from `mix-v4/train.jsonl` (already a
  validated diverse mix), ~60/40 target/anchor ratio matching honesty-v2's
  recipe. Zero collisions with any harness eval file, verified.
- **The target metric actually moved this time**: `mcq` 29.7% → 35.1%
  (+5.4pp vs baseline), where v1 had been exactly flat at 0.0pp. Verified
  the diagnosis, not just the hypothesis — a homogeneous single-template
  mix really was the problem. `arithmetic` flipped from a −4.0pp regression
  to a genuine +2.0pp improvement. `honesty` improved more plausibly
  (+3.0pp) than v1's suspicious, never-fully-explained +10pp jump.
- **Still not a clean acceptance-rule pass**: `format` (−3.3pp) and
  `variety` (−3.4pp) remain outside the 1-2pp tolerance vs. baseline, and
  `honesty_control` sits right at the edge (−2.8pp, one item out of 36).
  Full writeup: [eval/results/PILOT-iave-v2.md](eval/results/PILOT-iave-v2.md).
- **Caught my own mistake mid-eval**: launched the `iave-v2-ext` harness run
  while `iave-v2-control36` was still loading the model, without thinking
  about it - system free memory dropped to 4%, the exact crash pattern
  already documented in this journal for BF16-fused evals. Killed the
  second process (`kill -9`, plain `kill` didn't land first try) before it
  crashed anything, then ran the two sequentially as this project's
  established practice already dictates. No excuse for not following the
  project's own documented rule the first time.
- Real, direct precedent for the "not clean but improved" verdict:
  honesty-v2 itself wasn't a clean first-try pass either - it was ruled
  "borderline-pass pending a wider eval set" back on 2026-07-04 and only
  matured through v3/v4. iave-v2 is following the same shape, not failing
  in a new way.
- Leading hypothesis for why format/variety didn't recover: the 250 anchors
  were sampled uniformly at random from mix-v4, with no per-category
  balancing - if that draw under-represented format/variety examples
  relative to arithmetic/honesty, that would explain the asymmetric
  recovery. Next iteration (if pursued) should stratify the anchor sample
  by category explicitly instead of leaving it to chance.
- Standing pipeline rule reinforced (see IAVE section above): never train a
  LoRA on a single homogeneous sample type. Two independent confirmations
  now (honesty-v1, iave-v1) that this specific mistake produces the exact
  same failure signature - narrow style collapse leaking into unrelated
  categories - regardless of domain.

## 2026-07-10 — leis-pt objective 1 (training corpus) shipped: RAG-first, not closed-book QA

- Turned leis-pt's consolidated-legislation corpus into three HF datasets
  under `teex-pt`, gated (manual approval) and CC0-1.0 (official PT legal
  text is copyright-exempt by statute, a cleaner license situation than
  IAVE's `license: other` workaround needed):
  [leis-pt-consolidada](https://huggingface.co/datasets/teex-pt/leis-pt-consolidada)
  (base corpus, 1,727 diplomas),
  [amalia-sum-dre](https://huggingface.co/datasets/teex-pt/amalia-sum-dre)
  (diploma → official-summary SFT pairs, 1,006 diplomas),
  [amalia-cita-legal](https://huggingface.co/datasets/teex-pt/amalia-cita-legal)
  (grounded-citation-or-refusal SFT pairs, 8,668 examples). Each card
  documents its own scope, counts, and limitations.
- **Deliberately did not build closed-book legal QA.** leis-pt's own
  `PLANO.md` already argues the legal domain should be RAG-first
  (hallucination costs more than in an exam), and this project's own IAVE
  pilots are the empirical version of the same lesson - `iave-v1` flat at
  0.0pp on the mcq target, `iave-v2`'s fix only reached +5.4pp and still
  didn't clear the acceptance bar (see 2026-07-08 above). `amalia-cita-legal`
  trains grounded-answer-or-refuse instead of memorized recall, on purpose,
  and its refusal behavior is deliberately consistent with leis-pt's own
  production RAG service rather than invented independently. Confirmed
  this framing with Filipe via two `AskUserQuestion` rounds rather than
  assuming it.
- Gating is for access-tracking only here, not licensing uncertainty (that
  was IAVE's situation, not this one) - confirmed explicitly with Filipe.
- Extraction ran read-only against `~/Development/teex/leis-pt` per explicit
  instruction not to touch that repo; build scripts live in
  `pt-amalia/datagen/` but the extraction approach itself isn't detailed
  here or in the dataset cards, by request.
- Not yet done: decontamination against `LegalBenchPT` (the project's
  standing rule before any benchmark-reported training run), and the
  `datagen/` build outputs aren't committed to git yet - left for a
  separate ask.

## 2026-07-13 — legal-v1 LoRA pilot: RAG-first citation format lands, +66pp on target

- First actual training run on the leis-pt-derived datasets. Mix: legal
  citation + refusal examples, a slice of the summarization set, and
  general-purpose anchors (~60/40 target/anchor, the same anti-collapse
  ratio honesty-v2/iave-v2 established). New deterministic harness
  category (`legal_cita`/`legal_refusal`) added alongside `mcq` - same
  exact-match philosophy, no LLM judging.
- **Target metric: 16.0% → 82.0% (+66.0pp).** Baseline failures were
  almost all "extracted the right content but never used the citation
  tag" - confirmed this was a trainable format gap, not a grounding gap,
  before spending the training run on it. `legal_refusal` held at ceiling
  (100%→100%).
- Three secondary categories landed outside the project's strict
  1-2pp acceptance tolerance (`variety` -3.4pp, `honesty_control` -2.8pp,
  `mcq` -2.7pp) - each is a single flipped item, low power, but real.
  Verdict: BETTER, borderline-pass, the same shape as `iave-v2`'s own
  verdict, not a clean accept.
- **Ran `merge-75` (the current general-purpose champion) on the same new
  categories for comparison, which corrected one of my own conclusions
  before it went stale in the report:** I'd initially read the `mcq` dip
  as legal/exam cross-domain interference. `merge-75` - zero legal or exam
  training in its lineage - shows the identical -2.7pp, so that's generic
  adapter drift at this sample size, not something specific to legal-v1.
  `variety` is the real specific regression (`merge-75` +6.6pp on the same
  category legal-v1 -3.4pp) - likely the unstratified `mix-v4` anchor
  sampling, the same gap `iave-v2`'s own report flagged and never fixed.
  `legal_refusal` flipped the other way: `merge-75` (-10.0pp) is worse
  there than legal-v1 (0.0pp) - its dedicated refusal training helps
  exactly where the general-purpose checkpoint has no exposure.
- Two real infrastructure bugs hit and fixed along the way (now in
  project memory): `mlx_lm lora`'s training path has no memory ceiling
  unlike the harness's inference path, and OOM'd once on a config that
  looked safe on paper; and `transformers`' `apply_chat_template` can
  return a `BatchEncoding`, which fails an `isinstance(x, dict)` check and
  silently breaks any length-guard built on it.
- Published `adapters/legal-v1` to HF as `teex-pt/AMALIA-9B-0626-DPO-LoRA-legal-v1`,
  framed explicitly as a research pilot (not production-ready), same
  spirit as the honesty-pilot adapter release.
- Full report with the complete comparison table: `eval/results/PILOT-legal-v1.md`.

## 2026-07-13 (cont.) — legal-v2: same recipe, ~2x data, target climbs to 94% and variety fully recovers

- Considered merging `legal-v1` with `merge-75` to fix the `variety`
  regression, but decided to try more data first - cheaper to validate
  and doesn't foreclose the merge idea later. Checked `mix-v4`'s actual
  composition first: it has no distinct "variety" slice to stratify
  anchors by (variety looks like an emergent property of the data being
  pt-PT throughout, not a dedicated category) - the anchor-stratification
  fix proposed in the `legal-v1` report was murkier than first thought, so
  this run is data volume only, same anchor approach as `legal-v1`.
- Scaled the mix ~2x (700 grounded + 100 refusal + 400 sum-dre + 751
  anchors - the full `mix-v4` pool, up from 400 - vs. `legal-v1`'s
  350+50+200+400), 1,000 iters (~2x, same proportional-scaling precedent
  as `iave-v1`→`v2`). Same validated-safe recipe (batch 1, max-seq-length
  4096, grad-checkpoint) - peak memory landed at the same ~27.1GB as
  `legal-v1`, as expected since per-step memory doesn't depend on dataset
  size.
- **Target kept climbing with more data**: `legal_cita` 82.0%→94.0%
  (+12.0pp over `legal-v1`, +78.0pp over baseline). `legal_refusal` held
  at ceiling again.
- **`variety` fully recovered (83.3%→86.7%, ties baseline) without the
  stratification fix** - turned out `legal-v1` just used 400 of the 751
  available `mix-v4` anchors; using the full pool alone closed the gap.
  Simpler explanation than under-representation-by-category: it was
  under-sampling, not bad sampling.
- `honesty_control` and `mcq` landed at the exact same rate as `legal-v1`
  (0.0pp difference both ways) - reinforces they're low-power noise
  (1 flipped item each), not something more data should be expected to
  move. `honesty` regressed vs. `legal-v1` (78.0%→68.0%, -10.0pp) while
  still well above baseline (+18.0pp) - logged as a real but unexplained
  wobble, not investigated further this round.
- Only two categories remain outside strict 1-2pp tolerance
  (`honesty_control` -2.8pp, `mcq` -2.7pp), both already diagnosed as
  low-power noise via the `merge-75` comparison - closer to a clean
  accept than `legal-v1` or `iave-v2` ever reached.
- Full report: `eval/results/PILOT-legal-v2.md`.

## 2026-07-14 — legal-v2: external model comparison, then LegalBenchPT decontamination

- Compared `legal-v2` against general-purpose models on the same
  `legal_cita`/`legal_refusal` benchmark, zero-shot: Ministral-3-14B-Reasoning
  (22.0%), Mistral-Small-3.2-24B (4.0%, worse despite 2.5x the parameters),
  Claude Sonnet 5 (18.0%). None close to `legal-v2`'s 94.0%; model size
  doesn't predict this behavior at all.
- Built `harness/run_harness_anthropic.py` (Anthropic Messages API,
  `.env`/`python-dotenv` for the key, same `CHECKERS`/schema as
  `run_harness.py` for a directly comparable result) to also test a
  few-shot condition on Sonnet 5: the real leis-pt production system
  prompt (sent with explicit authorization - it's private-repo content,
  the auto-mode classifier correctly caught the first attempt without it)
  plus one training-set worked example. Result barely moved (18.0%→22.0%),
  but *why* is the actually useful finding: the `[F#]` tag syntax got
  picked up almost immediately (31→3 "no tag" failures), replaced by a
  much bigger new failure - refusals on genuinely grounded questions
  jumped from 10 to 36 of 50. Instruction + one demonstration teaches
  syntax, not calibration; that's what the LoRA's diverse positive/
  negative training examples are actually buying. All published to
  `teex-pt/AMALIA-9B-0626-DPO-LoRA-legal-v2`'s card, including two real
  pt-PT example responses.
- Then ran this project's long-deferred decontamination check against
  `LegalBenchPT` (`BeatrizCanaverde/LegalBench.PT`, already vendored
  locally under `amalia-lm-eval/`) - the standing rule from
  `PLANO-MELHORIA-AMALIA.md`, never done since `amalia-cita-legal`/
  `amalia-sum-dre` were first built. 13-word shingle overlap check
  (`datagen/decontaminate_legalbenchpt.py`) flagged 53/9,614 rows -
  every one individually verified as benign shared real-statute text
  (mostly short boilerplate phrases hitting many unrelated bench items at
  once; one 67-shingle outlier traced exactly to Artigo 214.º CRP,
  quoted verbatim on both sides of a constitutional-revision training
  example and independently in LegalBenchPT's public-finance questions).
  No fictional exam content ever appears in the training data. Verdict:
  clean. Full report: `eval/results/DECONTAMINATION-legalbenchpt.md`.
- Followed up immediately with `pt_exams` (`amalia-llm/pt_exams`, aka
  PHEB, 1,819 K-12 exam MCQs across 6 subjects) - same method
  (`datagen/decontaminate_pt_exams.py`, reusing the shingle utilities).
  Domain mismatch made near-zero overlap the expectation, confirmed not
  assumed: only 2/9,614 rows flagged, both the same training row matching
  the same bench item via two overlapping shingle windows of one shared
  phrase - traced to Resolução do Conselho de Ministros n.º 175/2017 (a
  real port-strategy policy), independently referenced by its official
  title in a 2019 Geography exam question. Verdict: clean. Full report:
  `eval/results/DECONTAMINATION-pt_exams.md`. Closes out `pt_exams`/
  `LegalBenchPT` for `amalia-cita-legal`/`amalia-sum-dre`; `alba` and
  `cultura_viva` (the other two consortium benchmarks) not yet checked -
  lower priority given even less topical overlap than `pt_exams` had.

## 2026-07-14 (cont.) — RAG integration test: real retrieval via lexbase.pt, the missing piece

- Every legal-domain eval so far tested citation behavior against a fixed
  synthetic excerpt set. This is the first test of the actual gap flagged
  after `legal-v2` shipped: real retrieval, real naturally-phrased
  questions, through the live production index rather than the offline
  harness.
- Filipe stood up `lexbase.pt` (leis-pt's production MCP retrieval
  service, public HTTP endpoint, 8 tools - 6 native
  `search_legislation`/`get_diploma`/`get_fragment`/`get_article`/
  `get_amendments`/`list_themes` plus a `search`/`fetch` pair for the
  OpenAI connector contract). Deliberately no generation/"answer" tool -
  retrieval only, by design, to avoid the liability of an embedded model
  giving legal advice. Registered via `claude mcp add`, but a brand-new
  MCP server added mid-session doesn't get picked up by an already-running
  session's tool registry - built a proper client instead
  (`harness/lexbase_client.py`, official `mcp` SDK, key in `.env`) rather
  than wait on a restart, since a reusable script is more valuable than a
  one-off manual tool call anyway.
- `harness/rag_integration_test.py` bridges retrieval to generation: calls
  `search_legislation`, formats real hits into the same `PERGUNTA:`/
  `EXCERTOS:` shape the SFT data uses, runs it through a local model. 10
  new, naturally-phrased questions (`harness/rag_test_queries.jsonl`),
  including one deliberately off-topic (a pastry recipe) to test refusal
  generalization somewhere training never touched.
- **Citation tag usage: baseline 1/10 real queries, `legal-v2` 9/10** -
  same diagnosis as the offline harness, now confirmed on genuinely new
  questions through the live index.
- **The off-topic query is the standout finding.** Both models correctly
  noticed the retrieved excerpts (gambling/bingo licensing, agricultural
  policy - genuinely irrelevant) didn't cover pastry recipes. Baseline
  said so, then answered the recipe anyway from general knowledge - real
  scope creep. `legal-v2` refused, in wording it was never trained on
  ("Consulte uma fonte dedicada à gastronomia portuguesa" vs. the trained
  template's "Consulte diretamente as fontes indicadas") - adapting the
  refusal *pattern* to a genuinely novel case, not reciting a memorized
  string. Stronger evidence of real calibration than the offline harness
  could show, since its refusal examples share a construction process
  with the training data.
- Also surfaced a real architectural fact, not specific to either model:
  retrieval never returned zero hits, even for the pastry question (still
  6 "closest" semantic matches). `lexbase.pt`'s empty-retrieval refusal
  shortcut essentially never fires in practice - the model's own judgment
  carries almost the entire relevance-calibration burden, which is
  exactly what this pilot was built to teach.
- Zero hallucinated citations across all of `legal-v2`'s real responses
  (checked programmatically: every `[F#]` used fell within the actual
  retrieved-hit range). One cosmetic-only artifact logged: some answers to
  plain questions still open with the training template's amendment-
  announcement framing even when the question isn't about an amendment -
  not a correctness issue, worth smoothing in a future iteration.
- Known gap: this test's prompt format doesn't include the breadcrumb
  `lexbase.pt`'s actual production prompt appends after the
  citation - tested the SFT training shape on purpose, not the exact
  production one yet. Full writeup: `eval/results/RAG-INTEGRATION-TEST.md`.

## 2026-07-14 (cont.) — RAG integration test closes both remaining gaps: production format + external models

- **Production prompt format tested** (`build_prompt(..., include_breadcrumb=True)`,
  matching `lexbase.pt`'s real shape): behaviorally equivalent to the
  training-shape run, 8/10 vs 9/10 strict-tag grounding, refusal held.
  The one delta is cosmetic - one response cited via unbracketed "F1"/"F2"
  markdown headers instead of `[F#]`, still correctly grounded, just
  invisible to a strict regex checker. Real minor robustness gap, not a
  behavioral regression.
- **Ran the same 10 real queries through every external model** (Ministral,
  Mistral-Small, Sonnet 5 via new `harness/rag_integration_test_anthropic.py`)
  for the full picture: tag usage baseline 1/10, Ministral 4/10,
  Mistral-Small 1/10, Sonnet 5 7/10, legal-v2 8-9/10.
- **This meaningfully nuances the earlier off-topic finding, honestly.**
  Sonnet 5 - which only scored 18-22% on the offline synthetic benchmark -
  correctly refuses the pastel-de-nata query here, zero-shot, no legal
  training. Question *style* matters a lot for a general model's zero-shot
  behavior: plain natural questions are closer to a general assistant's
  training distribution than the offline benchmark's amendment-summary
  phrasing. So the real, still-standing claim isn't "only legal-v2 can
  refuse correctly" (Sonnet 5 can too) - it's that legal-v2 matches or
  exceeds a frontier commercial model's grounding behavior on a small,
  9B, fully local model. Ministral and Mistral-Small (open-weight,
  similar/larger size) both still scope-creep into giving the recipe -
  Ministral's reasoning trace even states outright *"devo basear-me no
  meu conhecimento prévio"* - so this isn't just "any big/aligned model
  gets this right" either.
- Caught my own automated-check false positive before it went in the
  report: a naive keyword scan flagged Sonnet 5 as "gave the recipe"
  because its refusal used the word "ingredientes" while explaining what
  was *missing*. Manually read all six off-topic responses directly
  instead of trusting the heuristic - the discipline this project's
  journal keeps applying (verify before reporting, not just the numbers)
  caught it before publishing the wrong table.
- Full updated writeup: `eval/results/RAG-INTEGRATION-TEST.md`.

## 2026-07-14 (cont.) — RAG test: manual correctness review finds a real retrieval-vs-faithfulness tension

- Every check so far was format (citation tags) or calibration (refusal)
  - never whether the grounded answers are actually *right*. Manually
  read all 9 grounded queries' responses against the excerpts they cite
  (no gold answers exist for these natural queries, so this is
  faithfulness-to-source, not an independent legal review). 7/9 clean
  across every model.
- **The two exceptions are the real finding.** Q1 ("posso ser despedido
  por faltar sem justificação?") is a genuine cross-model disagreement -
  but it traces to retrieval missing CT Art. 351.º (the actual justa
  causa article), not to a model being wrong. `legal-v2`/baseline stayed
  strictly inside the (incomplete) shown text and said "não, a menos
  que..."; Sonnet 5/Mistral-Small filled the gap from background
  knowledge and said "sim, se grave/reiterada" - which matches the real
  law more completely but wasn't actually grounded in what they were
  shown. Real, worth-naming tension: strict grounding-faithfulness (this
  whole pilot's design goal) loses to correctness exactly when retrieval
  fails, and that's a limitation of the approach, not a bug to silently
  patch over.
- Q6 (pregnant-worker dismissal) looked like the same kind of split but
  wasn't - retrieval succeeded there, and "não, a menos que" vs. "sim,
  mas apenas" turned out to be two faithful readings of the same
  conditional-permission article, not a factual disagreement.
- Also caught a real but narrow generation-quality glitch: `legal-v2`'s
  Q4 answer opens with a garbled, repetitive sentence before recovering
  and citing correctly - cosmetic, unrelated to grounding, worth
  watching in a future iteration.
- Updated `eval/results/RAG-INTEGRATION-TEST.md` with the full review.

## 2026-07-14 (cont.) — Root-caused the Q1 retrieval gap: chunk dilution, not vocabulary

- Diagnosed directly against the live `lexbase.pt` service rather than
  guess. Three probe queries, escalating specificity: natural phrasing
  (fails), literal statutory phrasing "faltas não justificadas ao
  trabalho" (still fails), near-verbatim quote of the actual buried
  clause (still fails, doesn't even place in top 6). A direct quote of
  the source failing to retrieve its own source rules out vocabulary/
  phrasing gaps conclusively.
- `get_article` confirms CT Art. 351.º is correctly indexed - the real
  issue is that it's one long single-fragment article ("Noção de justa
  causa de despedimento") enumerating 13 lettered grounds, of which
  "faltas não justificadas" is just one (alínea g). Chunk-level dilution:
  the whole-article embedding represents "justa causa in general," so it
  loses to smaller single-topic "tipos de faltas" chunks whenever a query
  targets one specific enumerated ground.
- Gave concrete, priority-ordered feedback for the retrieval team:
  sub-chunk long enumerated articles at the alínea level (highest
  leverage, addresses root cause); treat this as a pattern to scan for,
  not a one-off patch (grounds/types/exemptions articles are common in
  PT statutory law); a weaker interim rerank-boost mitigation; and a
  ready-made regression test (the three probe queries + expected result)
  to verify any fix. Full diagnosis: `eval/results/RAG-INTEGRATION-TEST.md`.

## 2026-07-14 (cont.) — Decontamination complete: alba + cultura_viva clean, closes the standing rule

- Closed out the remaining two of the four consortium benchmarks
  (`datagen/decontaminate_alba_culturaviva.py`, same 13-word shingle
  method as `LegalBenchPT`/`pt_exams`): `alba` (240 Portuguese
  linguistics MCQs) and `cultura_viva` (1,000 Portuguese culture/trivia
  MCQs) both came back with zero overlap against `amalia-cita-legal`/
  `amalia-sum-dre`. Lower priority going in on the theory that
  linguistics puzzles and culture trivia have even less topical overlap
  with a legal-citation corpus than `pt_exams` already showed - played
  out that way, confirmed rather than assumed. Unlike the other two
  checks, nothing to manually verify (zero flagged rows on both).
- **All four consortium benchmarks now checked, all clean.** This was
  the one item explicitly requested and not yet done from the earlier
  "what's next" rundown - closed out today, not carried forward.
  Full report: `eval/results/DECONTAMINATION-alba-culturaviva.md`.
