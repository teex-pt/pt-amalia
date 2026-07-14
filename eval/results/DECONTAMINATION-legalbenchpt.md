# Decontamination check — LegalBenchPT (2026-07-14)

Standing project rule (`PLANO-MELHORIA-AMALIA.md`, `JOURNAL.md` "Standing
decisions"): decontaminate against the consortium benchmarks before any
dataset/training claim — deferred since `teex-pt/amalia-cita-legal` and
`teex-pt/amalia-sum-dre` were first built, run here for the first time.

## Method

Exact 13-word shingle overlap between the two training datasets (9,614
rows across train+valid) and `BeatrizCanaverde/LegalBench.PT` (4,723
items, 31 Portuguese legal domains, already vendored locally under
`amalia-lm-eval/tasks/amalia-bench/LegalBenchPT/`). 13-word windows is
the standard, cheap approach for literal text-reuse checks (same window
size popularized by GPT-3's own contamination methodology) — chosen over
embedding/topical similarity on purpose: LegalBenchPT's fictional exam
scenarios and our real-statute training data are *expected* to be
topically similar (both are Portuguese law), so a semantic-similarity
check would just measure "is this legal text," not actual reuse. A
literal 13-word run in common is a much stronger, low-false-positive
signal.

Not checked: `teex-pt/leis-pt-consolidada` (the raw corpus). It will
legitimately contain the same real statute text LegalBenchPT's questions
sometimes quote — that's expected overlap of public-domain law, not
contamination, and checking it would just flood the report with benign
hits on quoted articles rather than a meaningful signal. The two SFT
training sets are the actual decontamination target, since those are what
a model could memorize verbatim answers from.

## Result: 53/9,614 rows flagged, all verified benign on manual inspection

Raw counts alone would read as "contamination found" — the point of this
report is why they aren't, checked case by case rather than trusted as an
aggregate number:

- **Overlap size is small and scattered.** 52 of 53 hits matched only
  1-8 shingles (out of hundreds possible per row), and the matched phrase
  in every case is standard statutory boilerplate ("com pena de prisão
  até 2 anos ou pena de multa até 240...", "se pena mais grave lhe não
  couber por força de outra disposição legal...") that hits *multiple
  unrelated* LegalBenchPT items across the same domain simultaneously
  (e.g. one Código Penal phrase matched 5 different `Direito Penal`
  items). A genuine leaked test item would show one row matching heavily
  against *one specific* bench item, not a short common phrase scattered
  across many.
- **The one outlier is fully explained, not just plausible.** A single
  row (`cita-legal/train`, diploma `34520775`, a "Quarta revisão
  constitucional" tracking example) matched 67 shingles — 3x the next
  highest. Traced directly: this is Artigo 214.º da Constituição (the
  Tribunal de Contas' supreme oversight article), quoted verbatim in the
  training row (twice, from two amendment snapshots) and independently
  referenced by `LegalBenchPT`'s `Direito das Finanças Públicas`
  questions — the same real constitutional article on both sides, not a
  leaked exam item.
- **No fictional exam content ever appears in our data.** LegalBenchPT's
  questions are invented case studies (fictional names, companies, fact
  patterns — e.g. "Camila", "Hugo", "Loja de Roupa Jet Set") built around
  real legal provisions. None of that invented scenario text appears
  anywhere in `amalia-cita-legal`/`amalia-sum-dre`, which is built
  entirely from real DR sumários and real fragment text — there's no
  mechanism by which it could.

**Verdict: clean.** No evidence of literal test-item reuse. The flagged
rows are the expected, benign signature of two datasets independently
quoting the same real Portuguese statutes — normal for any Portuguese
legal-domain corpus, not a training/benchmark leak.

## Script and full data

`datagen/decontaminate_legalbenchpt.py` — `datagen/decontamination-legalbenchpt-report.json`
has all 53 flagged rows with the matched shingle and bench item IDs, for
anyone who wants to re-verify a specific case.
