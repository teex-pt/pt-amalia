# IAVE exam corpus — K-12 tutor specialization line

Verified MCQ question+answer pairs from Portuguese national secondary
(Ensino Secundário, 12th grade) exams, for specializing AMALIA toward a K-12
tutor use case. Ground truth by construction: every answer comes from the
official IAVE marking scheme, never inferred by a model.

## Scope

- **Source:** [iave.pt](https://iave.pt/provas-e-exames/arquivo/arquivo-provas-e-exames-finais-nacionais-es/)
  (Instituto de Avaliação Educativa), verified live URLs — filenames aren't
  a predictable pattern, so links are hardcoded in `iave_registry.py`, not
  guessed.
- **Years:** 2024, 2025. Entirely outside `pt_exams`/PHEB benchmark coverage
  (2006–2023) by construction — see `PLANO-MELHORIA-AMALIA.md`'s
  decontamination note.
- **Subjects:** 26 of IAVE's secondary-level subjects (not just the 6 the
  benchmark covers).
- **Sessions:** 1ª Fase, 2ª Fase, Época Especial.
- **122 exam sittings, 244 PDFs** (exam paper + marking scheme pairs), 159 MB.

**Not covered (real gaps):** Ensino Básico (grades 1–9) has its own exam
streams — 9th-grade finals and younger-grade diagnostic tests — untouched
so far. A K-12 tutor in the full sense needs those too; see JOURNAL.md.

## Pipeline

1. `iave_download.py` — respectful, rate-limited, resumable download from
   the verified registry.
2. `iave_extract.py` — parses MCQ items only for v1 (open-response items
   carry grading rubrics, not direct answers — a different, harder
   extraction problem). Handles three observed marking-scheme formats
   (table, inline+letter, inline+"Versão 1/2"). Strips page-footer/next-page
   bleed-through ("Prova 501/1.ª F. • Página 12/ 15" + whatever follows the
   page break) from captured question text. **270/272 found MCQ items
   paired with question text (99% yield).**
3. `iave_build_mix.py` — converts to the project's standard `messages`
   schema. Two-version exams (shuffled options) produce two records each.
   **462 samples (416 train / 46 valid).**

## Known limitations

- **Math notation garbling.** `pdftotext`'s font handling mangles calculus/
  algebra notation (fractions, limits, derivatives) in some STEM items —
  confirmed by manual inspection, not by a content detector. Records from
  `Matematica A/B, Matematica Aplicada, Fisica e Quimica A, Geometria
  Descritiva A` carry `notation_risk: true` in `extracted.jsonl` (**115 of
  462, 25%**) so they can be filtered or reviewed separately. Plain-number,
  combinatorics, and geometry-by-figure items in these same subjects
  extract cleanly — the flag is a coarse per-subject signal, not per-item.
- **Page-footer bleed-through (found and fixed).** A manual spot-check
  turned up captured question text ending in things like `"Prova 501/1.ª
  F. • Página 12/ 15\n␌Teil C – Schreiben"` — the PDF's page footer plus
  whatever of the next page's header leaked across the page break, since
  `pdftotext -layout` linearizes pages back-to-back. Affected 90/265
  records (34%) before the fix. `iave_extract.py`'s `find_question_text()`
  now strips everything from `"Prova " + <3-digit exam code>` onward
  (verified: that exact token never appears as legitimate question prose).
  Yield actually rose slightly after the fix (97% → 99%) since a few
  records the footer had pushed over the 3000-char cap now parse cleanly.
- **Item-numbering collisions.** Exams are organized in groups (GRUPO I/II/
  III, PARTE A/B/C) whose item numbering restarts, so the same number can
  refer to different items. Fixed by requiring at least two `(A)/(B)/...`
  markers in the matched text before accepting a pair — this trades some
  recall (a genuine MCQ under a reused number can be missed if an earlier,
  wrong-group occurrence also happens to look MCQ-shaped) for avoiding the
  worse failure of a wrong ground-truth label. Verified against one caught
  false positive during development (see JOURNAL.md).
- **Open-response items are entirely excluded from v1.** These carry the
  richest content (multi-level grading rubrics with model-answer
  descriptors) but aren't simple answer keys — using them well needs either
  rubric-conditioned generation (closer to our two-stage synthetic pipeline)
  or treating the top rubric level as loose guidance. Left for a follow-up.
