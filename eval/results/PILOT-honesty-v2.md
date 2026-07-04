# Piloto LoRA v2 — mistura corretiva (2026-07-04)

Segunda iteração do ciclo do plano §4, aplicando a receita do relatório v1:
mistura em vez de vetor único, menos treino, mais diversidade de templates.

- **Dataset (525 amostras):** 300 recusas (pools expandidos: 10 templates de
  recusa vs 4 na v1) + 91 QA de entidades reais on-policy (respostas do próprio
  AMALIA base, mantidas apenas se passam o gate anti-recusa+keywords; 1 rejeitada)
  + 134 âncoras verificadas do pipeline (69 aritmética, 65 formato, drafts
  Ministral com 89% de yield).
- **Treino:** `mlx_lm.lora`, 250 iters (vs 400), batch 2, 16 camadas, ~19,9 GB
  pico, ~10 min.

## Resultados

| Categoria | Baseline | v1 | **v2** | v2 vs baseline |
|---|---|---|---|---|
| honesty | 43,3% | 86,7% | **70,0%** | **+26,7pp** ✅ |
| **controlo (entidades reais)** | 100% | 66,7% | **100%** | **restaurado** ✅ |
| format | 73,3% | 70,0% | **80,0%** | +6,7pp ✅ |
| variety | 86,7% | 86,7% | **93,3%** | +6,7pp ✅ |
| arithmetic | 60,0% | 36,7% | **53,3%** | **−6,7pp** ⚠️ |
| **overall** | 65,8% | 70,0% | **74,2%** | **+8,4pp** |
| GSM8K-pt (25, flexible) | 48,0% | — | _(a medir)_ | — |

## Veredicto: quase — aritmética ainda fora da regra

Ambas as catástrofes da v1 corrigidas: o over-refusal desapareceu (12/12
entidades reais respondidas, sem alucinar nomes dos templates) e as fatias
âncora até **subiram** format e variety acima do baseline. A honestidade mantém
+26,7pp — menos espetacular que os +43pp da v1, mas sem os danos.

O bloqueio: aritmética recuperou de 36,7% para 53,3% mas continua 6,7pp abaixo
do baseline (= 2 itens em n=30; stderr ~±9pp). Segundo sinal (GSM8K-pt com o
adapter) em medição — resultado a preencher quando terminar.

## Receita v3 (leads)

- Mais âncora aritmética (69 → ~150) e eventualmente menos recusas (300 → 200).
- Avaliar o checkpoint intermédio (iter 100/150) — a interferência pode crescer
  com o treino.
- Considerar âncora de aritmética com exemplos de *raciocínio curto correto*
  (não só resposta seca) para proteger o circuito de cálculo.
- Baseline de aritmética com n maior antes de v3, para apertar a barra de ruído.

## Nota metodológica

Com n=30/categoria os deltas de 1 item são ±3,3pp — a regra de aceitação de
1–2 pontos exige amostras maiores para vetores em disputa. Antes da v3, gerar
um conjunto de avaliação aritmética alargado (n≥100, seeds novas, nunca usadas
em treino).
