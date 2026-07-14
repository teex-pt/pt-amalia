---
license: cc0-1.0
language:
- pt
task_categories:
- text-generation
- summarization
- text-retrieval
tags:
- portuguese
- pt-pt
- legal
- legislation
- government
- cc0
pretty_name: leis-pt — consolidated Portuguese legislation corpus
extra_gated_heading: Request access
extra_gated_prompt: >-
  This dataset compiles official Portuguese legislation text. The
  underlying content is public and copyright-exempt (see License below);
  access is gated only so we can track who's using it and for what — briefly
  tell us your intended use.
extra_gated_button_content: Request access
---

# leis-pt — consolidated Portuguese legislation corpus

One record per **consolidated** Portuguese legal act — the law as currently
in force, with amendments applied — sourced from Diário da República's
official consolidated-legislation records. Compiled by `leis-pt`, a
separate, private project (not published), and released here as a
training-ready corpus by [teex-pt/pt-amalia](https://github.com/teex-pt/pt-amalia).

This is the base corpus for two derived training sets — see
[teex-pt/amalia-sum-dre](https://huggingface.co/datasets/teex-pt/amalia-sum-dre)
(summarization) and
[teex-pt/amalia-cita-legal](https://huggingface.co/datasets/teex-pt/amalia-cita-legal)
(grounded citation / RAG training) — both built directly from this corpus.

## Scope

- **1,727 unique diplomas** — 26 base legal codes (Código Civil, Código
  Penal, Código do Trabalho, ...) plus 1,701 other consolidated acts
  (decree-laws, portarias, leis) reachable from Diário da República's
  by-code and by-theme consolidated-legislation indexes.
- **Consolidated / current-in-force text only** — not the full historical
  Diário da República stream. See Known limitations.
- 96.2M characters total, median 25.8K chars/diploma, up to 1.38M chars for
  the largest codes.
- Snapshot date: most recently updated through 2026-07.

## Files

- `corpus.jsonl` — one record per diploma:
  - identity/metadata: `diploma_id`, `diploma_legis_id`, `tipo`, `numero`,
    `designacao` (official descriptive title), `titulo`, `sumario`
    (official DR abstract), `emissor`, `data_publicacao`,
    `data_ultima_consolidada`, `eli` (European Legislation Identifier),
    `fonte_url`, `url_pdf`, `consolidacao_estado`, `is_codigo_base`,
    `temas` (theme tags from DR's own taxonomy)
  - `texto_integral` — the full consolidated text, linearized from the
    fragment tree (article/chapter headers + body text, document order)
  - `fragmentos` — the raw fragment tree (`id`, `pai_id`, `ordem`, `nome`,
    `epigrafe`, `texto`, `data_entrada_vigor`) for consumers that want
    structure (article-level chunking, amendment timestamps) rather than
    flat text
  - `n_fragmentos`, `n_chars`

## Known limitations

- **Consolidated law only, not the full historical stream.** Acts that only
  *amend* another act without themselves having a consolidated version
  aren't included as their own record — though the amendments they made
  are still reflected in `amalia-cita-legal`.
- **No historical "atos" PDF stream text extraction yet** — a real,
  currently-open gap upstream, not something this snapshot works around.
- Three diplomas (of 1,727) have no theme tag.

## License & attribution

Official Portuguese legal texts are exempt from copyright under Portuguese
law (Código do Direito de Autor e dos Direitos Conexos, art.º 8.º —
official acts of a public nature are excluded from copyright protection).
This compilation — the crawl, structuring, and deduplication — is released
under **CC0 1.0** (public domain dedication). Please retain the
`fonte_url`/`eli` provenance fields if you redistribute derived data, so
downstream users can trace any record back to its official publication.

## Citation

```
@misc{leis-pt-consolidada-2026,
  title = {leis-pt: consolidated Portuguese legislation corpus},
  author = {teex-pt},
  year = {2026},
  howpublished = {\url{https://huggingface.co/datasets/teex-pt/leis-pt-consolidada}},
  note = {Source: Diário da República, legislação consolidada (diariodarepublica.pt)}
}
```
