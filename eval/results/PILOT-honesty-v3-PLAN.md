# Piloto v3 — plano (2026-07-04)

Objetivo duplo: (1) recuperar o headroom de honestidade que a v2 sacrificou
(v1 provou que 86,7% é alcançável; v2 ficou em 70% para eliminar os danos) e
(2) apertar a medição para que o veredicto não dependa de 2 itens em n=30.

## Fase A — Medição primeiro (antes de qualquer treino)

O gargalo da v2 foi estatístico: com n=30/categoria, 1 item = ±3,3pp, mas a
regra de aceitação fala em 1–2 pontos. Antes de treinar:

1. **Harness alargado**: aritmética n=100 e honestidade n=100 (seeds novas,
   gama reservada p/ avaliação, nunca usadas em treino); controlo de entidades
   reais 12 → 36; format/variety mantêm n=30.
2. **Re-baseline** do modelo original no conjunto alargado (~1h no Mac).
3. **Re-avaliar o adapter v2** no mesmo conjunto — dá o delta real da v2 com
   stderr ±5pp e serve de comparação directa para a v3.
4. Regra de aceitação recalibrada: aritmética dentro de ±3pp do baseline
   alargado; controlo 100%; restantes ≥ baseline−2pp.

## Fase B — Dataset v3 (~750 amostras)

| Fatia | v2 | v3 | Racional |
|---|---|---|---|
| Recusas (fake/futuro) | 300 (57%) | **200 (27%)** | reduzir dominância; pools 10→14 templates |
| QA entidades reais (on-policy, gated) | 91 | **150** | pool 46→80 entidades; equilíbrio ~1:1 recusar-falso vs responder-real |
| **Pares fronteira (NOVO)** | — | **120** | gémeos quase idênticos: «Eça de Queirós» (real→responde) vs «Eça de Vasconcelos» (fake→recusa). Construíveis por mutação de apelido. Ensinam a *fronteira*, não o padrão superficial — ataca diretamente o modo de falha da v1 |
| Âncora aritmética | 69 | **180** | e com *raciocínio curto* (1 linha + resposta), não só resposta seca — proteger o circuito de cálculo, não apenas o estilo |
| Âncora formato | 65 | **100** | manteve/subiu format na v2; manter dose |

Notas:
- Âncoras: Ministral drafts com variante de prompt «explica numa linha e dá a
  resposta»; verificação = resposta correta + brevidade (≤25 palavras).
- Tudo verificado por código; seeds de treino disjuntas das de avaliação.
- DPO fica fora da v3 (mlx-lm não tem DPO no CLI); é a via natural na 4060 Ti
  com axolotl — track paralelo no desktop, não bloqueia.

## Fase C — Treino

- `mlx_lm.lora`, batch 2, 16 camadas, LR 1e-5 (inalterados — funcionaram).
- **300 iters com avaliação de checkpoints intermédios** (100/200/300): o
  harness alargado de aritmética+honestidade corre em ~20 min por checkpoint;
  escolher o sweet spot antes da avaliação completa. A v2 nunca verificou se
  250 já era tarde demais.

## Fase D — Avaliação e aceitação

- Checkpoint vencedor: harness completo alargado + controlo (36) + GSM8K-pt
  (limit 50, não 25) + `ifeval-mt-pt` (25) como canário de regressão.
- **Alvos**: honestidade ≥ 80% com controlo 100%; aritmética ±3pp; format ≥
  78%; variety ≥ 90%; GSM8K dentro do ruído.

## Custos estimados (tudo no M5 Pro)

| Fase | Tempo |
|---|---|
| A — harness alargado + re-baseline + re-eval v2 | ~2h30 compute |
| B — geração (âncoras Ministral dominam) | ~2h30 |
| C — treino + 3 checkpoints parciais | ~1h15 |
| D — avaliação final | ~1h30 |
| **Total** | **~8h — uma tarde + noite, desatendido** |

## Riscos conhecidos

- Pares fronteira podem confundir se a mutação colidir com pessoa real —
  mitigar com apelidos raros + verificação rápida de não-existência via
  contagem de resultados (ou aceitar ruído residual pequeno).
- Mais âncora aritmética pode diluir honestidade — é exatamente o trade-off
  que os checkpoints intermédios da Fase C vão mapear.
