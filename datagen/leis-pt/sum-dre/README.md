---
license: cc0-1.0
language:
- pt
task_categories:
- summarization
- text-generation
tags:
- portuguese
- pt-pt
- legal
- legislation
- sft
- summarization
- cc0
pretty_name: AMALIA sum-dre — Portuguese legal act summarization (SFT)
extra_gated_heading: Request access
extra_gated_prompt: >-
  This dataset is derived from official Portuguese legislation text (public,
  copyright-exempt — see License below). Access is gated only so we can
  track who's using it and for what — briefly tell us your intended use.
extra_gated_button_content: Request access
---

# AMALIA sum-dre — Portuguese legal act summarization (SFT)

`(diploma full text → official sumário)` instruction-tuning pairs, built for
specializing [AMALIA-9B](https://huggingface.co/amalia-llm/AMALIA-9B-0626-DPO)
toward Portuguese legal text. Ground truth by construction: every target
summary is Diário da República's **own official abstract** (`sumário`) for
the act, never inferred by a model. Derived from
[teex-pt/leis-pt-consolidada](https://huggingface.co/datasets/teex-pt/leis-pt-consolidada)
by [teex-pt/pt-amalia](https://github.com/teex-pt/pt-amalia).

## Why this exists

This project's own IAVE LoRA pilots (see `JOURNAL.md` in pt-amalia) showed
closed-book *fact-recall* SFT on small legal/exam data has a low ceiling —
format moved, precision didn't. Summarization is a different kind of task:
it trains compression and extraction *given the source text right there in
context*, not recall of facts the model has to have memorized. It's also
the task PLANO.md's leis-pt spec names first (`amalia-sum-dre`) as
"gold by construction."

## Scope

- **1,006 diplomas**, capped to those whose full consolidated text fits a
  single training context window (≤32,000 characters). The 721 diplomas
  above that cap — mostly the 26 base legal codes and a handful of omnibus
  reform laws — are a different task (retrieval source, not a
  single-summary target); see
  [teex-pt/leis-pt-consolidada](https://huggingface.co/datasets/teex-pt/leis-pt-consolidada)
  and [teex-pt/amalia-cita-legal](https://huggingface.co/datasets/teex-pt/amalia-cita-legal)
  instead.
- **956 train / 50 valid**, split by diploma (each diploma contributes
  exactly one row, so this is diploma-disjoint by construction — no
  leakage to guard against).

## Files

- `train.jsonl`, `valid.jsonl` — the project's standard chat schema:
  `{"messages": [{"role": "user", "content": "<instruction + diploma
  header + full text>"}, {"role": "assistant", "content": "<official
  sumário>"}]}`. Each record also carries `diploma_id`, `tipo`, `numero`,
  `designacao`, `fonte_url`, `n_chars_input` for traceability/filtering.
- `build-report.json` — yield stats (kept vs. skipped-too-long vs.
  skipped-empty).

## Known limitations

- **`valid.jsonl` is for SFT trainer loss monitoring**, not a benchmark —
  it's a random diploma-level split, not curated for difficulty or topic
  balance.
- The official `sumário` is itself sometimes terse (a single sentence) —
  this trains extractive/compressive summarization in the DR abstract's own
  house style, not a general-purpose summarizer.
- **Decontaminated against `LegalBenchPT` and `pt_exams`** (2026-07-14,
  13-word shingle overlap check): flagged rows all manually verified as
  benign shared real-document text (statutes, and one shared government
  policy title), not leaked test items — full reports:
  `eval/results/DECONTAMINATION-legalbenchpt.md` and
  `eval/results/DECONTAMINATION-pt_exams.md` in
  [teex-pt/pt-amalia](https://github.com/teex-pt/pt-amalia). `alba` and
  `cultura_viva` (the other two consortium benchmarks) not yet checked.

## License & attribution

Same basis as
[teex-pt/leis-pt-consolidada](https://huggingface.co/datasets/teex-pt/leis-pt-consolidada):
official Portuguese legal texts (including their official DR abstract) are
copyright-exempt (CDADC art.º 8.º). This compilation is released under
**CC0 1.0**.

## Citation

```
@misc{amalia-sum-dre-2026,
  title = {AMALIA sum-dre: Portuguese legal act summarization SFT pairs},
  author = {teex-pt},
  year = {2026},
  howpublished = {\url{https://huggingface.co/datasets/teex-pt/amalia-sum-dre}},
  note = {Target summaries sourced from Diário da República's official sumário field}
}
```
