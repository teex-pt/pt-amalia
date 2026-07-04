# leis-pt — corpus integral da lei portuguesa (especificação v0)

Projeto autónomo (futuro repo próprio, e.g. `teex-pt/leis-pt`); o pt-amalia
consome-o como fonte (`amalia-qa-legal`, `amalia-sum-dre`, registo formal).

## Decisão estrutural: duas formas da lei, dois produtos

1. **Atos (stream histórico):** cada diploma como publicado no DR — imutável,
   datado, com sumário oficial. É o registo histórico e a matéria-prima de
   sumarização verificável.
2. **Legislação consolidada (estado atual):** a lei em vigor com alterações
   aplicadas (diariodarepublica.pt/dr/legislacao-consolidada/ — confirmado
   acessível). É o que um sistema jurídico realmente consulta. Inclui o grafo
   de alterações/revogações entre diplomas — o ativo mais valioso para
   legal-tech.

## Modelo de dados (por diploma)

```
id, tipo (lei, decreto-lei, portaria, ...), número, data, série,
órgão emissor, sumário oficial, texto integral, estado de vigência,
altera -> [ids], alterado_por -> [ids], revoga -> [ids], revogado_por -> [ids],
url_oficial, url_pdf, versões consolidadas (quando existam)
```

## Fontes verificadas (2026-07-04)

| Fonte | Estado | Uso |
|---|---|---|
| `files.diariodarepublica.pt/1s/AAAA/MM/NNNNN/*.pdf` | ✅ padrão enumerável confirmado | PDFs Série I born-digital |
| `diariodarepublica.pt/dr/legislacao-consolidada/...` | ✅ confirmado | lei em vigor + grafo de alterações |
| API aberta do arquivo.pt | rota do consórcio AMALIA | histórico dre.pt (décadas) |
| EUR-Lex/CELLAR | bulk aberto | direito UE em pt-PT (fatia separada) |
| `stjiris/portuguese-legal-sentences` (HF, Apache 2.0) | ✅ pronto | jurisprudência STJ complementar |

## Fases

- **F0 — piloto (1 dia):** harvester de um mês de Série I (PDFs → texto) +
  20 diplomas consolidados; validar parsing, estrutura, sumários.
- **F1 — Série I completa born-digital (±1990→hoje):** crawl com rate-limit
  respeitoso; texto + metadados + sumários.
- **F2 — consolidada completa + grafo:** todos os códigos e diplomas em vigor,
  arestas altera/revoga.
- **F3 — histórico profundo (arquivo.pt + OCR dos PDFs digitalizados).**

## Licenciamento

Textos oficiais isentos de direito de autor (CDADC art.º 8). Dataset publicado
com dedicação CC0 sobre a compilação, com nota de proveniência. Crawl
respeitoso (rate-limit, User-Agent identificado, horário noturno).

## Reutilização no pt-amalia

- `amalia-sum-dre`: (texto do diploma → sumário oficial) — sumarização com
  gold por construção.
- `amalia-qa-legal`: QA ancorado com verificação extrativa.
- Registo formal para a categoria variedade/estilo.
- Descontaminar contra `LegalBenchPT` antes de treinar.
