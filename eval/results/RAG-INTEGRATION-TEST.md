# RAG integration test — real retrieval via lexbase.pt, not the offline harness (2026-07-14)

Every legal-domain eval so far (`PILOT-legal-v1.md`, `PILOT-legal-v2.md`,
the external-model comparisons) tested citation behavior against a fixed,
synthetic excerpt set (`harness/legal_cita_prompts.jsonl`, built from
amendment-summary-style questions). None of it tested the actual missing
piece: real retrieval quality, plus genuinely novel, naturally-phrased
user questions, through the live production index.

## Setup

- **Retrieval:** `lexbase.pt`'s production MCP service (`search_legislation`,
  `k=6`) — leis-pt's live, deployed retrieval layer, hybrid dense+sparse+BM25
  over the real consolidated-legislation index. New client:
  `harness/lexbase_client.py`.
- **Generation:** local, via `harness/rag_integration_test.py` — retrieved
  hits formatted into the same `PERGUNTA:`/`EXCERTOS:` shape the SFT
  training data uses (`amalia-cita-legal`'s citation format, no
  breadcrumb), then run through AMALIA baseline and `legal-v2` with no
  system prompt (matching how the training data itself has none).
- **Queries:** 10 genuinely new, naturally-phrased Portuguese legal
  questions (`harness/rag_test_queries.jsonl`) — none derived from
  amendment sumários, none seen in any training or eval data. One
  deliberately off-topic ("qual é a receita tradicional do pastel de
  nata?") to test refusal generalization to something with zero training
  precedent.
- **No automated scoring.** Real retrieval has no fixed gold excerpt set
  to check tag validity against the way the offline harness does — this
  is a qualitative review (n=10), not a statistically powered eval.

## Findings

**Citation tag usage: baseline 1/10 queries, legal-v2 9/10.** Matches the
offline harness's own diagnosis (baseline extracts the right content but
rarely tags it) at real-retrieval scale, on genuinely new questions the
model has never seen phrased this way.

**The off-topic query is the most informative single result.** Both
models correctly noticed the excerpts (bingo/gambling licensing,
education, agricultural policy — genuinely irrelevant) didn't answer a
question about pastry recipes. What each did next differs completely:

- **Baseline said so, then answered anyway** — switched to general
  knowledge and gave the actual pastel de nata recipe. Real scope creep:
  exactly the failure mode a grounded legal assistant can't have.
- **legal-v2 refused, in a phrasing it was never trained on**: "Não
  consigo fundamentar uma resposta nos excertos encontrados. Consulte uma
  fonte dedicada à gastronomia portuguesa." — the trained refusal
  template is "Consulte diretamente as fontes indicadas"; substituting
  "uma fonte dedicada à gastronomia portuguesa" for a food question is
  the model adapting the *pattern*, not reciting a memorized string. No
  refusal training example was ever about food. This is stronger evidence
  of generalized calibration than anything the offline harness could show,
  since the offline eval's refusal examples are drawn from the same
  construction process as the training refusals.

**Zero hallucinated citations.** Every `[F#]` tag `legal-v2` used across
all 10 real queries fell within the actual retrieved-hit range — checked
programmatically, not just spot-read.

**Retrieval quality itself looks solid.** E.g. "posso ser despedido por
faltar ao trabalho sem justificação?" and "uma empresa pode despedir uma
trabalhadora grávida?" both surfaced the directly relevant Código do
Trabalho articles at rank 1 — consistent with leis-pt's own stated
validation ("despedimento por justa causa" → CT Art. 351.º).

**A real architectural finding, not specific to either model:** retrieval
never returned zero hits, even for the pastel-de-nata query (still got 6
"closest" semantic matches). That means `lexbase.pt`'s empty-retrieval
refusal shortcut (`total=0` → fixed refusal, model never called) doesn't
actually fire for most off-topic questions in practice — dense retrieval
usually finds *something*. The burden of judging relevance falls on the
model almost every time, not on a retrieval-layer shortcut. That makes
`legal-v2`'s demonstrated calibration (not just its citation format) the
operationally important part of this pilot, not a secondary detail.

**One cosmetic artifact worth naming:** some `legal-v2` answers to plain
natural-language questions (e.g. the pregnant-worker query) still open
with the training template's framing ("A alteração introduzida por Lei
n.º 100/2009... incide sobre...") even though the user's question wasn't
about an amendment at all. Not a correctness problem — the citation and
content are right — but a style mismatch worth smoothing in a future
training iteration if this is deployed behind a real chat interface.

## Update: production prompt format tested (closes the first known gap)

`harness/lexbase_client.py`'s `build_prompt()` now supports
`include_breadcrumb=True`, matching `lexbase.pt`'s actual production
shape (`f"{citation} — {breadcrumb}"`) rather than only the SFT training
shape. Re-ran `legal-v2` on the same 10 queries with the production
format (`rag-results-rag-legal-v2-prod.jsonl`):

- **Behaviorally equivalent to the training-format run**: 8/10 queries
  grounded with a strict `[F#]` tag (vs. 9/10 without the breadcrumb),
  refusal still held cleanly on the off-topic query.
- **The one difference is cosmetic, not a regression.** Query 1 dropped
  its `[F#]` brackets and cited via markdown headers instead ("**F1** -
  Regime do Contrato..."), still correctly grounded in the right two
  excerpts — a strict downstream checker (this project's own
  `check_legal_cita`, or any regex-based consumer) would miss this as
  "no citation," even though a human reader wouldn't. Confirmed this
  wasn't a broader pattern: only 1/10 responses showed the discrepancy
  between a strict `\[F(\d+)\]` match and a loose `\bF(\d+)\b` match.
  **Real, minor robustness gap worth fixing** (a training example or two
  with a longer/breadcrumb-heavy `EXCERTOS` block, or a more tolerant
  citation-tag parser downstream) before calling this deployment-ready —
  not a reason to doubt the underlying grounding.

## Update: external models on the same real-retrieval queries

Ran the same 10 queries (production prompt format) through every model
from the offline-harness comparison, plus built
`harness/rag_integration_test_anthropic.py` (same `build_prompt`, Anthropic
Messages API) for Sonnet 5. Off-topic column = whether the model actually
produced the pastel de nata recipe (verified by reading every response,
not by keyword search — an early automated heuristic false-positived on
Sonnet 5's response, which explains what's *missing* using the word
"ingredientes" without ever giving any).

| Model | Tags used (/10) | Off-topic query |
|---|---|---|
| AMALIA-9B baseline | 1/10 | ❌ gave the recipe |
| Ministral-3-14B-Reasoning | 4/10 | ❌ gave the recipe (explicitly: *"devo basear-me no meu conhecimento prévio"*) |
| Mistral-Small-3.2-24B | 1/10 | ❌ gave the recipe immediately, no hedge at all |
| Claude Sonnet 5 | 7/10 | ✅ refused correctly |
| **legal-v2** | **8-9/10** | ✅ refused correctly |

**This nuances the earlier finding, in an honest direction.** On the
offline synthetic benchmark, Sonnet 5 scored only 18-22% on `legal_cita`
— but on these natural, plainly-phrased real questions it grounds
correctly 7/10 times and handles the off-topic case cleanly, much better
than its offline-benchmark showing suggested. Question *style* matters a
lot for a general model's zero-shot citation behavior: the offline
benchmark's amendment-summary-style questions ("Regula a criação e o
regime de...") are further from a general assistant's training
distribution than plain user questions ("Posso ser despedido por...").
So the honest claim isn't "only `legal-v2` can refuse correctly" — Sonnet
5 does too, zero-shot, with no legal-specific training. **The real,
still-standing differentiator is that `legal-v2` matches or exceeds a
frontier commercial model's grounding behavior on a small, 9B model that
runs entirely locally** — not that grounded refusal is uniquely hard
without fine-tuning. Ministral and Mistral-Small (open-weight, similar or
larger size to AMALIA-9B) both fail the same off-topic test baseline
does, so this isn't just "any sufficiently large/aligned model gets this
right" either — it's specifically the smaller open-weight models that
struggle, frontier-scale alignment or targeted fine-tuning both seem to
work.

## Update: manual correctness review (closes the "grounding correctness" gap)

No gold answers exist for these natural queries, so this is a manual
read of every grounded response against what the retrieved excerpts it
cites actually say — checking *faithfulness to the shown text*, not an
independent doctrinal legal review. 7 of 9 grounded queries (Q2, Q3, Q5,
Q7, Q8, Q9) were accurately grounded across every model that cited —
claims matched the quoted article text with no fabrication. Two are
worth detailing:

- **Q1 ("posso ser despedido por faltar ao trabalho sem justificação?")
  is a genuine model disagreement, but it's a retrieval problem, not a
  model problem.** The 6 retrieved excerpts miss CT Art. 351.º (the
  actual "justa causa" dismissal-grounds article confirmed earlier this
  session) — retrieval surfaced tangential articles instead (a
  public-sector retaliation presumption, the *employer's* own
  court-no-show consequences, old-CT absence-type classifications).
  Given that gap, `legal-v2`/baseline stayed strictly inside what the
  shown text states and answered "não, a menos que..." — `legal-v2`
  explicitly notes *"Não diz que a falta sem justificação leva
  automaticamente ao despedimento"* (correct: the shown excerpts really
  don't say that). Sonnet 5/Mistral-Small answered "sim, pode... se
  grave ou reiterada," reasoning from background knowledge that happens
  to match the real (unretrieved) law more completely. **Real tension
  worth naming, not resolving one way:** strict grounding-faithfulness
  (what this pilot trains for) loses to actual correctness exactly when
  retrieval itself fails to surface the authoritative source. A citation
  discipline this strict is a feature when retrieval works and a
  limitation when it doesn't.
- **Q6 ("pode despedir uma trabalhadora grávida?") looked like a
  disagreement but isn't one.** Retrieval succeeded here (CT Art. 51.º,
  the real protection article, was hit #1). Art. 51.º establishes a
  *conditional* permission — dismissal only with prior mandatory
  approval, presumed unjustified without it. "Não, a menos que..."
  (baseline/`legal-v2`) and "sim, mas apenas..." (Sonnet 5/Mistral-Small)
  are both faithful readings of the same real provision — just which
  side of the same conditional a model leads with. Not a factual error
  on either side.
- **One real generation-quality glitch, unrelated to grounding:**
  `legal-v2`'s Q4 answer opens with a garbled, repetitive sentence
  ("deve ser fundamentada apenas no(s)(s)(s) contexto(s) relevante(s)...
  no(a)s(s) transcrições(s)...") before recovering and citing correctly.
  Cosmetic, not a citation-validity or grounding problem, but a real
  fluency issue worth watching for in a future iteration.

## Known gaps in this test

- ~~The empty-retrieval refusal path (`total=0`) was never exercised —
  every query in this set returned hits, including the off-topic one.~~
  **Closed below — retrieval team shipped a fix that makes this
  reachable, verified in production.**
- ~~Only tested one off-topic query — worth a small set of them (different
  domains: medical, general trivia, other-country law).~~ **Closed below.**
- The Q1 retrieval gap is itself worth a follow-up: is `search_legislation`
  systematically weaker on "can I be fired for X" phrasing than on
  "justa causa"-style legal terminology? One example isn't enough to
  conclude a pattern. **Update: root-caused, see below — it's not a
  phrasing/vocabulary gap.** **Further update: the shipped fix does NOT
  close this specific case — see below, it targets a different part of
  the same root cause.**

## Update: retrieval fix verified live in production, scaled off-topic test (2026-07-14)

The retrieval team's fix for the chunk-dilution root cause (previous
section) is deployed on `api.lexbase.pt` — confirmed directly against the
live MCP endpoint, not assumed from a changelog. Re-ran the three
reproducible probe queries from the root-cause diagnosis:

| Probe query | Before | After (live) |
|---|---|---|
| Near-verbatim quote of CT Art. 351.º alínea g | Not in top 6 | **Rank #1** (`in_force_only=True`) |
| Literal statutory phrasing ("faltas não justificadas ao trabalho") | Not in top 6 | Still not in top 6 |
| Natural phrasing ("faltar ao trabalho sem justificação") | Not in top 6 | Still not in top 6 |

**The fix resolves the exact regression case it targeted (verbatim/
strong-signal queries), not the softer paraphrases of the same
question.** The original Q1 finding — retrieval misses Art. 351.º, so a
strictly-grounded model answers from incomplete context — **still stands
for natural phrasing**, confirmed by re-running Q1 unchanged: same
citation set as the original test, same hedged "não, a menos que..."
answer. Not a failure of the fix; it targeted a different, narrower slice
of the same underlying problem than Q1's phrasing sits in.

**Bonus, unplanned fix bundled in the same deploy:** a separate, larger
bug where `vigente` (in-force) status only checked suspension, not
repeal — 86,903/86,905 indexed fragments were flagged "in force,"
including the entire repealed pre-2009 Código do Trabalho, which then
outranked the current Code in results. Confirmed fixed live: the old
Código do Trabalho's equivalent article now returns `vigente: false` with
a repeal citation, and is excluded by the API's default
`in_force_only=true` filter.

**Scaled the off-topic set from 1 query to 5, spanning domains the
original test never touched** (medical dosage, entertainment trivia,
foreign-country economic law, foreign-country geography, in addition to
the original recipe question) — all 5 correctly return `total: 0` live,
same as the original pastel-de-nata case. The abstention gate the fix
introduces (a cross-encoder confidence threshold, replacing a
fusion-score that was documented as anti-correlated with relevance)
generalizes beyond the one query originally tested.

**But the same gate produces a genuine false-abstention on an in-corpus,
answerable question**, caught only because it was one of the original
10 queries and therefore had a known-good prior result to regress
against: "Quanto tempo tenho para devolver um produto comprado online?"
used to return 6 hits (the correct EU consumer-rights transposition
article ranked #1); now returns `total: 0`. Root-caused directly against
the retriever: the correct article is still found and still ranks #1
among candidates, but its cross-encoder logit (−1.84) falls just under
the −1.0 abstention threshold — a calibration gap for this question's
phrasing style ("devolver um produto" vs. the article's own vocabulary,
"livre resolução do contrato"), not a retrieval miss. **Worth flagging
back to the retrieval team**: the threshold's own calibration note
already warns keyword-style queries score far lower than question-style
ones and required deliberately mixing both into the calibration set —
this looks like a third style (indirect/paraphrastic natural questions)
that the current calibration set may not cover, and one held-out example
isn't enough to say how often this recurs in real traffic.

**New failure mode found, present in both models, not caused by the
retrieval fix:** asked about *Brazilian* labor law ("O que diz a lei
brasileira sobre férias de trabalhador?"), retrieval correctly has
nothing Brazilian to offer (the corpus is Portuguese-law-only) but
surfaces topically-matching Portuguese Código do Trabalho articles
instead of abstaining — and **both baseline and legal-v2 answer as if
those provisions were Brazilian law**, without noticing the jurisdiction
mismatch ("A lei brasileira sobre férias de trabalhador, prevista no
Código do Trabalho..." — that Código do Trabalho is Portugal's). This is
a real correctness failure, distinct from the off-topic case: the topic
matches, so nothing signals "wrong corpus" to either the retriever (no
jurisdiction field to gate on) or the model (never trained to check
whether a cited code's own jurisdiction matches the question's). Not
tested in the original 10 queries; worth a small follow-up set (other
Lusophone countries — Angola, Cabo Verde, Brazil again with different
phrasing) to see how often this recurs before treating it as a one-off.

## Root cause of the Q1 retrieval gap: chunk-level dilution, not vocabulary

Diagnosed directly against the live service (`get_article` + three probe
queries), not guessed:

1. Natural phrasing ("faltar ao trabalho sem justificação") → CT Art.
   351.º not retrieved. `bm25` absent entirely (zero lexical overlap);
   dense scores for all 6 returned hits cluster tightly (0.65-0.68, no
   real separation).
2. **Literal statutory phrasing** ("faltas não justificadas ao
   trabalho") → still not retrieved. Surfaces generic "tipos de faltas"
   classification articles instead.
3. **Near-verbatim quote of the actual target clause**
   ("faltas não justificadas que determinem prejuízos ou riscos graves
   para a empresa" — Art. 351.º alínea g)'s own wording) → *still* not
   retrieved, even in the top 6. This rules out vocabulary/synonym gaps
   conclusively: a direct quote of the source failing to retrieve its
   own source means the problem isn't what words the query uses.

`get_article` confirms Art. 351.º is correctly indexed as a single
fragment: one long article ("Noção de justa causa de despedimento")
containing a general clause plus **13 lettered grounds (a-m)** —
disobedience, rights violations, conflicts, property damage, false
declarations, unjustified absences (g), safety violations, violence,
etc. — all in one chunk. That chunk's embedding represents "justa causa
in general," diluted across 13 unrelated grounds, so it consistently
loses to smaller, single-topic chunks (dedicated "tipos de faltas"
articles) whenever a query targets *one* specific ground rather than the
general concept. This is a **chunking granularity problem specific to
long enumerated-list articles**, not a retrieval-algorithm or embedding-
quality problem — and very likely not unique to this one article, since
"grounds for X" / "types of Y" enumerated articles are a common pattern
in Portuguese statutory law (termination grounds, aggravating/mitigating
circumstances, exemptions, etc.).

**Feedback for the retrieval team, in priority order (status as of the
2026-07-14 production check, see update above):**

1. ~~Sub-chunk long enumerated-list articles at the alínea level.~~ **Not
   what shipped, and that's fine — the deployed fix took a different,
   arguably better route to the same root cause: guaranteed
   per-retriever candidate-pool slots (so a decisive single-retriever
   match can no longer be evicted before the cross-encoder judges it)
   plus a query-focused passage window for the cross-encoder (so a long
   article's relevant alínea isn't truncated away). No re-chunking of
   the corpus needed. **Verified fixed for verbatim/strong-signal
   queries; natural-phrasing paraphrases of the same question (Q1-style)
   are still not fixed by this** — worth deciding whether that residual
   gap needs its own follow-up or is an acceptable remaining edge.
2. **Scan for other long, single-fragment articles with many lettered
   sub-items — still open**, the shipped fix reduces the blast radius
   (any retriever's strong signal now reaches the judge) but doesn't
   verify every such article individually the way sub-chunking would
   have guaranteed by construction.
3. ~~Cheaper interim mitigation: rerank boosting for
   "definition/grounds"-pattern epígrafes.~~ **Superseded** — the
   shipped fix's guaranteed-pool + focused-window approach addresses the
   same gap more directly than a ranking band-aid would have.
4. **New, from the production check**: the abstention threshold has at
   least one confirmed false-abstention on an in-corpus answerable
   question (see update above, "Quanto tempo tenho para devolver um
   produto comprado online?") — a calibration gap for indirect/
   paraphrastic natural-question phrasing, not a retrieval miss (the
   correct article is still found and ranked #1, just under the cutoff
   logit). The calibration note already flags that keyword-style and
   question-style queries score very differently and both had to be
   included deliberately — this looks like a third style the current
   calibration set may be missing. Worth scoring real query-log traffic
   against the threshold before trusting the 0-false-abstention
   calibration number for phrasing this indirect.
5. **New, from the production check**: no jurisdiction signal —
   `search_legislation` returns Portuguese law for jurisdiction-mismatched
   queries (e.g. "a lei brasileira sobre X") whenever the topic matches,
   with nothing to indicate the corpus has no Brazilian content at all.
   Neither model catches this itself (see update above). Not a
   regression from anything tested before; a newly-found gap, likely
   worth a metadata-level fix (flag/abstain when a query names a
   non-Portuguese jurisdiction) rather than a model-training fix, since
   the retrieval layer is the one place that actually knows the corpus's
   coverage.
6. **Reproducible test cases to hand off directly**, no need to
   re-derive them: the three original probe queries
   (`harness/lexbase_client.py --query "..."`) for the chunk-dilution
   regression test (now passing for the verbatim-quote query only), plus
   the "devolver um produto" false-abstention query and the "lei
   brasileira" jurisdiction query as two new named regression cases to
   track going forward.

## Update: both open findings fixed in the retrieval codebase (2026-07-14, pending deploy)

The two findings above (feedback items 4 and 5) are now fixed in
`teex-pt/lexbase-be` (commit `c3bb211`), verified end-to-end against the
local retriever on the production scoring configuration — **not yet live
on `api.lexbase.pt` until the box deploys it**:

- **False-abstention**: root cause was a calibration-set gap — indirect
  consumer phrasing is a query *style*, and it scores whole logits below
  the question-style gold queries the original threshold was fitted on,
  even when the correct article ranks #1. The threshold was re-fitted on
  a new 84-query, 5-style calibration set (now a rerunnable script + a
  tracked query file, so the next new style is a re-fit, not
  archaeology). The re-fit also surfaced that the original fit had
  silently measured the wrong numeric configuration on macOS (a
  quantization-engine selection bug, also fixed). After the re-fit, the
  "devolver um produto" query returns the correct consumer-rights
  article, all off-topic probes still refuse — including a new
  adversarial probe that *looks* answerable but isn't (a traffic-fine
  question whose statute isn't in the corpus), which now bounds the
  threshold from below.
- **Jurisdiction conflation**: unfixable at the ranking layer (the
  Portuguese article on the same topic *genuinely is* the most
  topically-relevant candidate — "impostos em Espanha" scored above any
  viable threshold), so it's now a coverage check in the service layer,
  which is the one place that knows what the corpus contains. Explicit
  foreign-law phrasing ("lei brasileira", "código civil espanhol") and
  foreign-situation locations ("férias em Angola") refuse before
  retrieval with an explanatory `note` the calling model can relay;
  queries with any Portugal anchor sail through, so "posso contratar um
  trabalhador brasileiro em Portugal?" still returns Portuguese law
  (top hit: CT art. 8.º, destacamento — correct). 33 fire/no-fire cases
  plus this report's full query set verified end-to-end.

Re-verify both against the live endpoint after the next deploy — the
threshold is fitted on a different CPU kernel family than production
runs, and the original fit survived that transfer once but it should be
confirmed, not assumed.

## Files

`harness/lexbase_client.py`, `harness/rag_integration_test.py`,
`harness/rag_integration_test_anthropic.py`, `harness/rag_test_queries.jsonl`,
`harness/rag_test_queries_v2.jsonl`,
`harness/rag-results-rag-{baseline,legal-v2,legal-v2-prod,ministral,mistral-small,sonnet5}.jsonl`,
`harness/rag-results-rag-{baseline,legal-v2}-v2-scale.jsonl`.
