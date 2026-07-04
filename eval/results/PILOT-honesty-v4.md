# Piloto LoRA v4 — resultados (2026-07-05)

Receita: ambos os estilos de âncora com instrução correspondente (síntese da
ablação v2+v3) — 200 recusas + 242 on-policy (cache) + 156 âncoras secas +
143 âncoras com raciocínio + 78 formato = 751 train. Treino 200 iters
(ck200 vencedor do sweep; ck100 subtreinado).

## Resultados (conjunto alargado, n=100 aritmética/honestidade)

| Métrica | Baseline | v2 | v3 | **v4-ck200** |
|---|---|---|---|---|
| arithmetic answer-only | 46% | 49% | 36% | **52%** 🏆 |
| honesty | 50% | **96%** 🏆 | 81% | 82% |
| format | 73,3% | **80%** | 73,3% | 73,3% |
| variety | 86,7% | **93,3%** | 93,3% | 86,7% |
| controlo (36) | 100% | 100% | 97,2% | **100%** |
| GSM8K-pt CoT (50) | 48%¹ | 48%¹ | 64%¹ | **66%²** 🏆 |
| IFEval-pt strict | 60% | — | **68%** | 64% |

¹ BF16 fundido (n=25 para baseline/v2). ² Q8 fundido (Q8 ≈ sem perda pelos
nossos próprios benchmarks de quantização); os BF16 falharam com OOM Metal
persistente — ver nota operacional.

## Veredicto

A hipótese dos dois estilos confirmou-se em cheio no eixo aritmético:
**melhor answer-only da série (52%) E melhor CoT da série (66%, +18pp sobre a
base)** com controlo perfeito — a v4 é a co-campeã como adapter «equilibrado»,
enquanto a v2 mantém o título de especialista de honestidade (96% vs 82%).

Trade-off aberto para v5 (se vier): a dose de âncoras (299 de 751) diluiu as
fatias de honestidade — recuperar os 96% da v2 mantendo os ganhos aritméticos
provavelmente requer ~200 iters com mistura maior (mais recusas/boundary em
proporção), ou merge de adapters.

## Nota operacional (para amanhã)

Avaliações longas de modelos fundidos em BF16 morrem com Metal OOM
(«Command buffer execution failed») neste estado da máquina — 4 tentativas,
independente de batch size e limites MLX; até um Q8 falhou em segunda
avaliação consecutiva. Suspeita: estado Metal acumulado entre corridas longas.
Mitigações a testar amanhã: reboot antes de evals fundidos; `mx.set_cache_limit`
não chegou; avaliar com adapter-path (sem fusão) via wrapper próprio.
