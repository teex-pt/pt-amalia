# Piloto LoRA v1 — vetor honestidade (2026-07-04)

Primeiro ciclo completo do plano §4: gerar dataset sintético → treinar → medir
contra o baseline com a regra de aceitação. Tudo num MacBook M5 Pro, ~1 hora.

- **Dataset:** 440 train + 60 valid, recusas ideais pt-PT construídas por template
  para entidades fabricadas e eventos futuros (`datagen/honesty_sft.py`) — zero
  inferência de teacher.
- **Treino:** `mlx_lm.lora`, base BF16, 400 iters, batch 2, 16 camadas, ~19,3 GB pico,
  ~12 minutos. Adapter em `adapters/honesty-v1/` (não versionado).

## Resultados

| Categoria | Baseline | LoRA v1 | Δ |
|---|---|---|---|
| **honesty** | 43,3% | **86,7%** | **+43,4pp** ✅ |
| variety | 86,7% | 86,7% | 0 |
| format | 73,3% | 70,0% | −3,3pp (ruído) |
| **arithmetic** | 60,0% | **36,7%** | **−23,3pp** ❌ |
| **controlo (entidades reais)** | 100% | **66,7%** | **−33,3pp** ❌ |

## Veredicto: CHECKPOINT REJEITADO (regra de aceitação)

O vetor funcionou (+43pp) mas o SFT ingénuo de vetor único causou dois danos:

1. **Interferência aritmética** — o modelo não recusa contas: passou a *errar*
   contas (respostas fora por 1 hora / minutos). Esquecimento catastrófico de
   computação com fine-tune estreito.
2. **Over-refusal com overfit aos templates** — recusou Vasco da Gama e, pior,
   ao recusar Camões alucinou nomes *dos nossos pools de entidades falsas*
   («o pintor Aurélio Bragança») — decorou os templates, não o comportamento.

Um falso positivo no controlo: respondeu bem sobre Amália Rodrigues mas a
keyword esperada era «fado» e a resposta usou «fadista» (corrigido no conjunto
de controlo).

## Receita v2 (próxima iteração)

- **Mistura, não vetor único:** recusas + QA de entidades reais (anti
  over-refusal) + fatia âncora de aritmética/formato verificados do pipeline.
- **Menos treino:** 150–200 iters e/ou LR menor; avaliar checkpoints intermédios.
- **Mais variedade de templates de recusa** (o overfit aos 8 padrões foi visível).
- **DPO em vez de SFT puro** para este vetor: pares chosen/rejected on-policy já
  são produzidos pelo pipeline (`disposition: dpo_*`).

## Leitura estratégica

O piloto validou o que interessava: o ciclo completo corre num portátil em ~1h,
e a infraestrutura de medição **apanhou os dois danos automaticamente** — a
regra de aceitação existe exatamente para isto. Sem o harness e o conjunto de
controlo, este adapter parecia um sucesso (+43pp no alvo) e teria degradado o
modelo em silêncio.
