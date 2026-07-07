# Piloto LoRA iave-v2 — âncoras de diversidade (2026-07-08)

Correção direta ao diagnóstico do iave-v1 (eval/results/PILOT-iave-v1.md):
vetor único, sem âncoras, causou interferência cruzada. Réplica da correção
honesty-v1→v2 (misturar âncoras de outras categorias), aplicada ao corpus
IAVE.

- **Dataset:** `datagen/build_iave_v2_mix.py` — todas as 383 amostras IAVE
  (train) + 250 âncoras amostradas aleatoriamente de `mix-v4/train.jsonl`
  (aritmética, formato, honestidade, variedade, QA on-policy — já um mix
  validado e diverso), proporção ~60/40 alvo/âncora, replicando a receita
  honesty-v2. 633 train + 62 valid. Zero colisões com qualquer ficheiro de
  avaliação do harness (verificado).
- **Treino:** `mlx_lm.lora`, base BF16, 300 iters (escalado de 200 do v1,
  proporcional ao mix 1.65x maior), batch 2, 16 camadas, lr 1e-5, ~21,3 GB
  pico, ~5,5 min. Train loss 2,391→0,748; val loss 6,909→0,758 (curva
  saudável). Adapter em `adapters/iave-v2/` (não versionado).

## Resultados (vs. baseline, vs. iave-v1)

| Categoria | Baseline | iave-v1 | iave-v2 | v2 vs baseline | v2 vs v1 |
|---|---|---|---|---|---|
| **mcq (IAVE, o alvo)** | 29,7% | 29,7% | **35,1%** | **+5,4pp** ✅ | +5,4pp |
| arithmetic | 46,0% | 42,0% | **48,0%** | **+2,0pp** ✅ | +6,0pp |
| format | 73,3% | 66,7% | 70,0% | −3,3pp ❌ | +3,3pp |
| honesty | 50,0% | 60,0% | 53,0% | +3,0pp ✅ | −7,0pp |
| variety | 86,7% | 83,3% | 83,3% | −3,4pp ❌ | 0,0pp |
| controlo (honesty_control, 36 itens) | 100% | 97,2% | 97,2% | −2,8pp ❌ | 0,0pp |

## Veredicto: MELHOR, mas ainda NÃO passa a regra de aceitação estrita

A regra ("harness pt-PT sobe; internacionais/controlo não descem mais de
1-2pp") continua a falhar em `format` (−3,3pp) e `variety` (−3,4pp) vs.
baseline, e `honesty_control` fica na margem (−2,8pp, um único item em 36).
Não é um "aceite" limpo.

Mas o diagnóstico do iave-v1 está agora **validado empiricamente, não só
hipotetizado**: a métrica-alvo, que tinha ficado exatamente parada em
0,0pp no v1, moveu-se **+5,4pp** aqui — a mesma correção (misturar âncoras)
que resolveu honesty-v1 produz o mesmo tipo de efeito no IAVE. `arithmetic`
passou de regressão (−4,0pp) a melhoria real (+2,0pp). `honesty` melhorou de
forma mais moderada e plausível (+3,0pp) do que o salto suspeito de +10pp do
v1 (que nunca foi bem explicado — provavelmente arrastado pelo mesmo colapso
de estilo que causou as outras regressões).

`format` e `variety` não recuperaram. Hipótese mais provável, a confirmar
numa próxima iteração: as 250 âncoras foram amostradas aleatoriamente de
`mix-v4`, sem controlo de proporção por categoria — se a amostra por acaso
sub-representou exemplos de formato/variedade relativamente a aritmética/
honestidade, isso explicaria a assimetria de recuperação por categoria.

**Precedente direto no próprio projeto:** honesty-v2 (2026-07-04) também não
foi um "aceite" limpo à primeira — foi classificado como "borderline-pass
pendente de um conjunto de avaliação mais amplo" e só amadureceu ao longo de
v3/v4. Este resultado segue o mesmo padrão, não é um caso isolado.

## Nota de poder estatístico

`mcq` (n=37): erro-padrão ≈ ±7,5pp. `honesty_control` (n=36): um único item
= 2,8pp. As diferenças aqui são reais o suficiente para orientar a próxima
iteração, mas pequenas demais para tratar qualquer categoria individual como
definitivamente resolvida ou definitivamente por resolver.

## Próximos passos (se prosseguir)

1. Amostrar âncoras por categoria explicitamente (não aleatoriamente) —
   garantir cobertura mínima de `format` e `variety` no mix v3.
2. Considerar mais iterações dado o mix maior (300 pode ainda estar
   sub-treinado para 633 amostras mais diversas que as 383 homogéneas do
   v1).
3. Dado o corpus IAVE é pequeno (270 itens verificados) comparado ao
   pipeline sintético de honestidade (que teve 4 iterações para maturar),
   vale considerar se vale a pena continuar a iterar SFT paramétrico aqui
   versus investir esse esforço na direção RAG-first já identificada para
   leis-pt — a mesma lógica (dados de exame são conhecimento denso e
   específico, não um comportamento amplo como "não confabules") pode
   aplicar-se aqui também.
