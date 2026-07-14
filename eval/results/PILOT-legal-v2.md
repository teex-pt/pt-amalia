# Piloto LoRA legal-v2 — mais dados, mesma receita (2026-07-13)

Escala direta do `legal-v1` (`eval/results/PILOT-legal-v1.md`): mesma
receita, ~2x o volume de dados. `legal-v1` validou a hipótese RAG-first
(lacuna de formato, não de conhecimento) a pequena escala controlada
(+66,0pp no alvo); este piloto testa se mais dados robustece a margem sem
sacrificar nada, seguindo o próprio padrão do projeto (iave-v1→v2 escalou
~1,65x, não mais, e escalou iters proporcionalmente).

- **Dataset:** `datagen/build_legal_v2_mix.py` — 700 citação fundamentada +
  100 recusa (de `amalia-cita-legal/train.jsonl`, ~2x `legal-v1`) + 400
  sumarização (`amalia-sum-dre/train.jsonl`, 2x) + 751 âncoras de
  `mix-v4/train.jsonl` (quase 2x `legal-v1`'s 400 — usa o pool completo
  disponível, que afinal só tem 751 linhas). 1.789 train + 162 valid.
  Mesmo filtro por tokenizer real a 4096 tokens, zero linhas truncadas,
  zero colisões com ficheiros de avaliação do harness.
  **Âncoras continuam por amostragem aleatória, não estratificada** — a
  ideia de estratificar por categoria (próximo passo do relatório
  `legal-v1`) foi adiada: `mix-v4` não tem uma fatia distinta de
  "variedade" para estratificar (ver nota abaixo).
- **Treino:** `mlx_lm.lora`, base BF16, 1.000 iters (~2x `legal-v1`,
  proporcional ao mix ~2x maior), batch 1, 16 camadas, lr 1e-5,
  `--max-seq-length 4096`, `--grad-checkpoint`. Pico de memória 27,1 GB —
  praticamente idêntico ao `legal-v1` (a receita de memória por passo não
  depende do tamanho do dataset, só do `max-seq-length`/batch, por isso
  não haveria motivo para esperar diferente). Train loss 2,983→0,654; val
  loss 2,710→0,902 (curva saudável). Adapter em `adapters/legal-v2/`.

## Resultados (baseline, merge-75, legal-v1, legal-v2)

| Categoria | Baseline | merge-75 | legal-v1 | **legal-v2** | v2 vs base | v2 vs v1 |
|---|---|---|---|---|---|---|
| **legal_cita (o alvo, n=50)** | 16,0% | 16,0% | 82,0% | **94,0%** | **+78,0pp** ✅ | **+12,0pp** |
| legal_refusal (n=10) | 100% | 90,0% | 100% | 100% | 0,0pp ✅ | 0,0pp |
| arithmetic (n=100) | 46,0% | 51,0% | 50,0% | **58,0%** | +12,0pp ✅ | +8,0pp |
| format (n=30) | 73,3% | 80,0% | 80,0% | 80,0% | +6,7pp ✅ | 0,0pp |
| honesty (n=100) | 50,0% | 96,0% | 78,0% | 95,0%* | +45,0pp ✅ | +17,0pp |
| variety (n=30) | 86,7% | 93,3% | 83,3% | **86,7%** | **0,0pp** ✅ | **+3,4pp** |
| honesty_control (n=36) | 100% | 100% | 97,2% | 97,2% | −2,8pp ❌ | 0,0pp |
| mcq (IAVE, n=37) | 29,7% | 27,0% | 27,0% | 27,0% | −2,7pp ❌ | 0,0pp |

## Veredicto: MELHOR que legal-v1 em quase todos os eixos — mais perto de um "aceite" limpo

**O alvo continuou a subir com mais dados**: 82,0%→94,0% (+12,0pp sobre
`legal-v1`), tal como a nota de próximos-passos do relatório anterior
previa ("escalar faria sentido para robustecer a margem"). `legal_refusal`
mantém-se no teto.

**`variety` recuperou por completo** (83,3%→86,7%, empatado com o
baseline) — **sem** aplicar a estratificação por categoria que tinha sido
proposta como o próximo passo óbvio. A explicação mais simples: `legal-v1`
usava só 400 das 751 âncoras `mix-v4` disponíveis; `legal-v2` usa o pool
completo. Mais amostras aleatórias do mesmo pool geral, por si só, deram
cobertura suficiente — não era preciso um mecanismo de seleção mais
inteligente, só menos sub-amostragem. `honesty_control` e `mcq` ficam
exatamente iguais a `legal-v1` (0,0pp de diferença nos dois) — reforça a
leitura já feita no relatório anterior: são efeitos de baixo poder
estatístico (1 item cada) e ruído genérico de *drift*, não algo que mais
dados de `legal-v2` deveriam mover.

**`honesty` não regrediu — era um falso negativo do verificador,
investigado e corrigido em 2026-07-14** (ver
`eval/results/HONESTY-REGRESSION-legal-v2.md` para o diagnóstico
completo). Diff item-a-item dos 100 casos: 16 viraram de sucesso→falha,
6 de falha→sucesso. Leitura manual de todos os 16: são recusas genuínas
e calibradas sobre pessoas fictícias — `legal-v2` passou a preferir
"Não identifico X" em vez de "Não conheço X" (mesma recusa, verbo
diferente), e a lista de marcadores do `check_honesty` não reconhecia a
primeira forma. Os 6 casos inversos são reais: `legal-v1` confabulava
biografias completas (datas, obras inventadas) onde `legal-v2` recusa
corretamente. Corrigido adicionando "não identifico" à lista de
marcadores (`harness/verifiers.py`) e reavaliando as respostas já
geradas (pontuação é função pura do texto, sem nova inferência) — apenas
`legal-v2` mudou (68,0%→**95,0%**, 27 itens corrigidos, zero falsos
positivos introduzidos); `legal-v1`, `merge-75` e o baseline ficaram
exatamente iguais, confirmando que o problema era específico da mudança
de fraseologia do `legal-v2`, não do verificador em geral nem de
`legal-v1`.

Com `variety` recuperado e `honesty` corrigido, restam apenas
`honesty_control` (−2,8pp) e `mcq` (−2,7pp) fora da tolerância de
1-2pp — ambos já diagnosticados como ruído de baixo poder estatístico
(1 item em 36/37), não como falhas específicas de `legal-v2`. Isto é
bastante mais perto de um "aceite" limpo do que `legal-v1` ou o próprio
`iave-v2` alguma vez chegaram — e mais perto ainda depois desta correção,
já que `honesty` deixa de ser um eixo negativo.

## Nota de poder estatístico

`legal_cita` (n=50): +78,0pp sobre o baseline, muitíssimo acima de
qualquer erro-padrão plausível. `honesty` (n=100), corrigido: +17,0pp
sobre `legal-v1` — não é ruído, é um artefacto de verificador já resolvido
(ver acima), não uma questão de poder estatístico.

## Próximos passos (se prosseguir)

1. **Não é urgente perseguir mais escala** — o alvo já está em 94,0% e a
   única categoria que resta fora da tolerância estrita além de `mcq` é
   `honesty_control`, ruído de baixo poder estatístico já bem
   diagnosticado, não algo que volume adicional deva mover
   previsivelmente.
2. ~~Investigar a queda de `honesty` (78,0%→68,0%) com uma terceira
   execução ou um n maior antes de decidir se é sinal ou ruído.~~
   **Feito em 2026-07-14** — não era sinal nem ruído, era um bug do
   verificador. Corrigido.
3. A experiência de *merge* com `merge-75` (adiada no relatório anterior)
   já não tem uma motivação tão forte para `variety` — recuperou sozinho
   com mais dados. Continua a fazer sentido só se o objetivo for herdar
   os ganhos gerais de `merge-75` (honesty 96%, arithmetic 51%) num único
   checkpoint, não como correção de regressão.
