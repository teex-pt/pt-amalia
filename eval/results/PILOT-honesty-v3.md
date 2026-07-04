# Piloto LoRA v3 — resultados (2026-07-05)

Receita: 200 recusas + 150 QA reais + 92 pares fronteira + 143 âncoras
aritméticas **com raciocínio** + 78 formato (608 train / 55 valid), 300 iters
com sweep de checkpoints. Duas colisões train/eval foram apanhadas pelo guard
e corrigidas antes do treino (13 + 6 prompts — resampling e filtros em todas
as fatias; caching de fatias para reruns baratos).

## Sweep de checkpoints (subset n=50)

| Checkpoint | arithmetic | honesty |
|---|---|---|
| ck100 | 26,0% | 82,0% |
| ck200 | 26,0% | **90,0%** |
| ck300 | 26,0% | 24,0% ⚠️ colapso tardio |

Nenhum elegível (aritmética < 43%) — vencedor por fallback: ck100.

## Avaliação completa (ck100, conjunto alargado)

| Métrica (n) | Baseline | v2 | **v3-ck100** |
|---|---|---|---|
| honesty (100) | 50,0% | **96,0%** | 81,0% |
| arithmetic answer-only (100) | 46,0% | **49,0%** | **36,0%** ❌ |
| format (30) | 73,3% | **80,0%** | 73,3% |
| variety (30) | 86,7% | 93,3% | 93,3% |
| controlo (36) | 100% | **100%** | 97,2% |
| **GSM8K-pt CoT (50)** | 48,0%¹ | 48,0%¹ | **64,0%** ⬆ |
| **IFEval-pt strict (25)** | 60,0% | — | **68,0%** ⬆ |

¹ baseline/v2 medidos com n=25.

## Veredicto: REJEITADO como vencedor global — v2 mantém o título

Mas a v3 produziu a descoberta mais interessante dos três pilotos: **o estilo
das âncoras transfere para o estilo da tarefa**.

- v2 (âncoras resposta-seca) protege a aritmética answer-only (+3pp) e não
  mexe no GSM8K.
- v3 (âncoras com raciocínio) **melhora as tarefas com raciocínio pedido**
  (GSM8K CoT +16pp, IFEval +8pp) e **degrada o answer-only** (−13pp vs v2):
  o modelo aprendeu a responder curto saltando o raciocínio — e a calcular em
  silêncio é exatamente o que ele faz mal.
- Trata-se de uma ablação limpa: mesma mistura exceto o estilo das âncoras.

Outras lições: ck300 mostrou colapso tardio (parar às ~200 iters); o guard de
colisões disparou duas vezes e salvou a validade do pilot — e o caching de
fatias transformou reruns de 2h em 1 minuto.

## Hipótese v4 (bem fundamentada pelos dados v2+v3)

Âncoras nos DOIS estilos, cada uma com a instrução correspondente:
- pergunta «responde apenas com X» → resposta seca (protege answer-only, v2)
- pergunta «explica numa linha» → raciocínio curto (ganha CoT, v3)
- treino limitado a 200 iters (pico de honestidade, antes do colapso)

Custo marginal: fatias em cache; faltam só âncoras secas extra (~1h Ministral)
+ treino 12 min + avaliação ~2h.
