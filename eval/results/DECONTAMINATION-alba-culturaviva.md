# Decontamination check — ALBA and CulturaVivaPT (2026-07-14)

Closes out the remaining two of the four consortium benchmarks named in
this project's standing decontamination rule (`PLANO-MELHORIA-AMALIA.md`),
alongside `LegalBenchPT` and `pt_exams`
(`eval/results/DECONTAMINATION-legalbenchpt.md`,
`eval/results/DECONTAMINATION-pt_exams.md`). Same method: 13-word shingle
overlap between `amalia-cita-legal` + `amalia-sum-dre` (9,614 rows) and
each benchmark's full item set.

## Result: clean, zero overlap on both

- **ALBA** (`amalia-llm/alba_mcq`, 240 items — Portuguese linguistics
  MCQs: morphology, syntax, semantics, discourse, phonetics, lexicology,
  language variety, word play): 0 rows flagged.
- **CulturaVivaPT** (`amalia-llm/cultura-viva-pt-mcq`, 1,000 items —
  Portuguese culture/trivia MCQs: gastronomy, festivals, geography,
  heritage, literature, personalities, proverbs, sports): 0 rows flagged.

Lower priority than `LegalBenchPT`/`pt_exams` going in, and it played out
that way — linguistics puzzles and culture trivia have essentially no
topical overlap with a legal-citation corpus, and the check confirms it
rather than just assuming it. Unlike the other two checks, there were no
flagged rows to manually verify.

**All four consortium benchmarks now checked for `amalia-cita-legal`/
`amalia-sum-dre`: clean across the board.**

## Script and full data

`datagen/decontaminate_alba_culturaviva.py` —
`datagen/decontamination-alba-report.json`,
`datagen/decontamination-culturaviva-report.json`.
