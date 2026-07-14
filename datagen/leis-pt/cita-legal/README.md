---
license: cc0-1.0
language:
- pt
task_categories:
- question-answering
- text-generation
tags:
- portuguese
- pt-pt
- legal
- legislation
- sft
- rag
- grounded-qa
- cc0
pretty_name: AMALIA cita-legal — grounded legal citation SFT (RAG-first)
extra_gated_heading: Request access
extra_gated_prompt: >-
  This dataset is derived from official Portuguese legislation text (public,
  copyright-exempt — see License below). Access is gated only so we can
  track who's using it and for what — briefly tell us your intended use.
extra_gated_button_content: Request access
---

# AMALIA cita-legal — grounded legal citation SFT (RAG-first)

`(question + real source excerpts → answer that cites the exact article,
or a refusal when the excerpts don't answer the question)`. Built for
specializing [AMALIA-9B](https://huggingface.co/amalia-llm/AMALIA-9B-0626-DPO)
toward Portuguese legal text, as the *grounded-answering* counterpart to
[teex-pt/amalia-sum-dre](https://huggingface.co/datasets/teex-pt/amalia-sum-dre).
Derived from
[teex-pt/leis-pt-consolidada](https://huggingface.co/datasets/teex-pt/leis-pt-consolidada)
by [teex-pt/pt-amalia](https://github.com/teex-pt/pt-amalia).

## Why this exists (RAG-first, not closed-book)

leis-pt's own project spec concludes that in a legal domain, where
hallucinating is more costly than in an exam, it makes more sense to train
"a model that's good at *using* a search tool" than "a model that
memorized the law" — and this project's own IAVE LoRA pilots back that up
empirically: closed-book fact-recall SFT on small legal/exam data moved
answer *format*, not *precision* (rejected at 0pp on the mcq target; a
second pass reached only +5.4pp, still not a clean pass). So this dataset
does **not** train closed-book legal QA. Instead it trains the same
answer-only-from-context-or-refuse contract leis-pt's own retrieval service
already enforces in production, deliberately kept consistent with it
rather than reinvented.

## Ground truth by construction

- **Questions** are real, official summaries of amending laws (e.g.
  "Procede à segunda alteração à Portaria n.º 46/2015...") describing what
  each law actually changed — not synthesized by a model.
- **Answers** are templated, extractive citations of the real target
  article's text — no free-text generation, no model call anywhere in the
  pipeline, so there's no hallucination risk to inherit.
- **Refusals** pair a real question with excerpts from a genuinely
  unrelated diploma, answered with a fixed refusal string consistent with
  leis-pt's own production refusal behavior.

## Scope

- **7,538 grounded (positive) examples**, each with up to 6 source
  excerpts.
- **1,130 refusal (negative) examples** (~15% of the positive count) —
  real question, deliberately wrong excerpts.
- **8,222 train / 446 valid**, split **diploma-disjoint** (no diploma's
  examples appear on both sides) and balanced so a handful of
  heavily-amended codes (Código Civil, Código Penal, ...) can't dominate
  one split — applying the lesson from this project's own IAVE
  sitting-level leak (see that dataset's card) proactively rather than
  repeating it.
- A small fraction of source amendment records (~4%) couldn't be resolved
  to a specific article and were dropped rather than guessed — see
  `build-report.json`.

## Files

- `train.jsonl`, `valid.jsonl` — `{"messages": [{"role": "user", "content":
  "PERGUNTA: ...\n\nEXCERTOS:\n[F1] ...«...»\n..."}, {"role": "assistant",
  "content": "<grounded citation answer, or the refusal string>"}]}`. Each
  record also carries `target_diploma_id`, `label` (`grounded`/`refusal`),
  `n_fragments_available`, `n_fragments_used`.
- `build-report.json` — event/resolution/split yield stats.

## Known limitations

- **A small fraction of citations may point to the wrong instance of an
  article** when a diploma has more than one fragment sharing the same
  article label (rare) — folded into the same ~4% noise budget above, not
  separately quantified.
- **Answers are templated citations, not natural-language explanations.**
  This trains citation discipline and grounding, not conversational legal
  explanation — deliberately, to keep every answer verifiable against its
  source with zero generation risk.
- **`valid.jsonl` is for SFT trainer loss monitoring**, not a retrieval or
  QA benchmark — leis-pt's own hand-validated benchmark work ("Stage B")
  is tracked separately in that project, not here.
- **Decontaminated against `LegalBenchPT` and `pt_exams`** (2026-07-14,
  13-word shingle overlap check, 9,614 rows checked): 53 + 2 rows flagged
  respectively, all manually verified as benign shared real-document text
  (statutes and one shared government policy title), not leaked test
  items. No fictional exam content from either benchmark appears anywhere
  in this dataset. Full reports: `eval/results/DECONTAMINATION-legalbenchpt.md`
  and `eval/results/DECONTAMINATION-pt_exams.md` in
  [teex-pt/pt-amalia](https://github.com/teex-pt/pt-amalia). `alba` and
  `cultura_viva` not yet checked.

## License & attribution

Same basis as
[teex-pt/leis-pt-consolidada](https://huggingface.co/datasets/teex-pt/leis-pt-consolidada):
official Portuguese legal texts are copyright-exempt (CDADC art.º 8.º).
This compilation is released under **CC0 1.0**.

## Citation

```
@misc{amalia-cita-legal-2026,
  title = {AMALIA cita-legal: grounded Portuguese legal citation SFT pairs},
  author = {teex-pt},
  year = {2026},
  howpublished = {\url{https://huggingface.co/datasets/teex-pt/amalia-cita-legal}},
  note = {Questions and target text sourced from Diário da República's official records; templated, not model-generated}
}
```
