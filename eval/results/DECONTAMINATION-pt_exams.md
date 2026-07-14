# Decontamination check — pt_exams (2026-07-14)

Second half of the standing decontamination rule (`PLANO-MELHORIA-AMALIA.md`,
`JOURNAL.md` "Standing decisions"), following
`eval/results/DECONTAMINATION-legalbenchpt.md` — same method, against
`pt_exams` (`amalia-llm/pt_exams`, aka PHEB, 1,819 Portuguese high-school
exam MCQs 2006-2023 across six subjects: Portuguese, Mathematics A,
History A, Geography, Biology and Geology, Philosophy).

## Method

Same as the `LegalBenchPT` check: exact 13-word shingle overlap between
`amalia-cita-legal` + `amalia-sum-dre` (9,614 rows) and every `pt_exams`
question (`question` field + answer `choices`, so exact-string matches
count regardless of which side of the MCQ they land on).

## Result: 2/9,614 rows flagged, both the same benign case

Domain mismatch (K-12 subjects vs. our legal-text corpus) makes near-zero
overlap the expectation — confirmed, not just assumed: both flagged rows
are the *same* training row (`cita-legal/train`, diploma `176519653`)
matching the *same* bench item (`Geography`, 2019, question 5) via two
overlapping shingle windows of one shared phrase, not two independent
hits.

Traced directly: the training diploma is **Resolução do Conselho de
Ministros n.º 175/2017**, titled "Estratégia para o Aumento da
Competitividade da Rede de Portos Comerciais do Continente - Horizonte
2026" — a real government port-strategy policy. The 2019 Geography exam
question references this same real, named policy document in a question
about Tagus estuary navigability. Both sides are quoting the official
title of a real public document, not shared test-item content.

**Verdict: clean.** Combined with the `LegalBenchPT` check
(`eval/results/DECONTAMINATION-legalbenchpt.md`), this closes out the
`pt_exams`/`LegalBenchPT` portion of this project's standing
decontamination rule for `amalia-cita-legal`/`amalia-sum-dre`. `alba` and
`cultura_viva` (the other two consortium benchmarks named in
`PLANO-MELHORIA-AMALIA.md`) have not been checked — lower priority, since
both are general-culture/trivia benchmarks with even less topical overlap
with a legal-citation corpus than `pt_exams` already had.

## Script and full data

`datagen/decontaminate_pt_exams.py` — `datagen/decontamination-pt_exams-report.json`
has both flagged rows with matched shingles and bench item IDs.
