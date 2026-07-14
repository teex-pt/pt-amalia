# Piloto LoRA legal-v1 — citação jurídica fundamentada, RAG-first (2026-07-13)

Primeiro piloto de especialização jurídica, construído sobre
`teex-pt/amalia-cita-legal` e `teex-pt/amalia-sum-dre` (leis-pt, objetivo 1).
Deliberadamente **não** é QA jurídico de livro fechado — o próprio
`PLANO.md` do leis-pt conclui que o domínio jurídico deve ser RAG-first
(alucinar custa mais caro do que num exame), e os pilotos IAVE deste
projeto (iave-v1: 0,0pp no alvo; iave-v2: +5,4pp, ainda sem aceitação
limpa) são a versão empírica da mesma lição — SFT de memorização factual
em dados jurídicos/de exame pequenos tem um teto real. `legal-v1` treina
antes o contrato "responde só a partir do contexto fornecido, cita, ou
recusa-te explicitamente", o mesmo que o serviço RAG de produção do
leis-pt já aplica.

- **Dataset:** `datagen/build_legal_v1_mix.py` — 350 exemplos citação
  fundamentada + 50 recusa (amostra de `amalia-cita-legal/train.jsonl`) +
  200 sumarização (`amalia-sum-dre/train.jsonl`) + 400 âncoras de
  `mix-v4/train.jsonl` (aritmética, formato, honestidade, variedade),
  proporção ~60/40 alvo/âncora replicando a receita honesty-v2/iave-v2.
  917 train + 83 valid. Filtrado pelo tokenizer real (não por contagem de
  carateres) para caber em `--max-seq-length`, com substituição em vez de
  truncatura — nenhuma linha excede o limite. Zero colisões com qualquer
  ficheiro de avaliação do harness (verificado). Conjunto de avaliação
  determinístico próprio: `harness/legal_cita_prompts.jsonl` (50
  fundamentadas + 10 recusa), reservado por diploma antes do split
  train/valid, com dois novos verificadores exatos (`check_legal_cita`,
  `check_legal_refusal`) no mesmo espírito do `check_mcq`.
- **Treino:** `mlx_lm.lora`, base BF16, 500 iters, batch 1, 16 camadas,
  lr 1e-5, `--max-seq-length 4096`, `--grad-checkpoint`. Pico de memória
  27,1 GB. Train loss 3,590→0,725; val loss 2,070→0,870 (curva saudável,
  sem divergência). Adapter em `adapters/legal-v1/` (não versionado).
  **Nota de fiabilidade:** um primeiro smoke-test com `--max-seq-length
  6144`/batch 2 rebentou com OOM real do Metal ao iter 3 (pico 25,2 GB e a
  subir) — o caminho de treino do `mlx_lm.lora` não tem o teto de memória
  que `run_harness.py` aplica no caminho de inferência. Corrigido antes do
  treino completo, não durante. A execução completa também sofreu a mesma
  pressão de memória intermitente observada no resto desta sessão
  (lentificação, não falha) — iters 100→500 mediram ~62 min de relógio,
  mais lento do que o smoke-test isolado sugeria.

## Resultados (vs. baseline, vs. merge-75)

`merge-75` é o checkpoint recomendado atual para uso geral (alpha-blend
v2/v4, ver JOURNAL.md 2026-07-07). `legal-v1` não foi treinado sobre
`merge-75` nem o inclui — é um adapter independente sobre o BF16 base, tal
como `iave-v1`/`iave-v2` também foram, e a comparação serve para separar
"efeito genérico de qualquer adapter" de "efeito específico do domínio
jurídico". `merge-75` nunca tinha sido avaliado em `legal_cita`/
`legal_refusal`/`mcq` antes deste piloto — corrido agora para os três,
pela primeira vez.

| Categoria | Baseline | merge-75 | legal-v1 | m75 Δ | lv1 Δ |
|---|---|---|---|---|---|
| **legal_cita (o alvo, n=50)** | 16,0% | 16,0% | **82,0%** | +0,0pp | **+66,0pp** ✅ |
| legal_refusal (n=10) | 100% | 90,0% | 100% | −10,0pp ❌ | 0,0pp ✅ |
| arithmetic (n=100) | 46,0% | 51,0% | 50,0% | +5,0pp | +4,0pp ✅ |
| format (n=30) | 73,3% | 80,0% | 80,0% | +6,7pp | +6,7pp ✅ |
| honesty (n=100) | 50,0% | 96,0% | 78,0% | +46,0pp | +28,0pp ✅ |
| variety (n=30) | 86,7% | 93,3% | 83,3% | +6,6pp | −3,4pp ❌ |
| honesty_control (n=36) | 100% | 100% | 97,2% | 0,0pp | −2,8pp ❌ |
| mcq (IAVE, n=37) | 29,7% | 27,0% | 27,0% | −2,7pp | −2,7pp ❌ |

**A comparação com `merge-75` muda uma conclusão importante:** `mcq` cai
exatamente −2,7pp em `merge-75` também — o mesmo checkpoint que nunca viu
uma única amostra de treino relacionada com direito ou exames. Isto
invalida a leitura inicial (abaixo, mantida riscada por transparência) de
que seria "interferência cruzada entre especializações jurídica/exame".
Leitura mais correta: qualquer adaptador que se afasta do BF16 base custa
tipicamente ~1 item de `mcq` (n=37, poder estatístico baixo), seja qual for
o domínio de treino — um efeito genérico de *drift*, não algo específico
de `legal-v1`. `variety`, pelo contrário, **mostra agora divergência real**:
`merge-75` melhora-o (+6,6pp) enquanto `legal-v1` o regride (−3,4pp) — aqui
sim há um efeito específico da mistura `legal-v1` (âncoras `mix-v4`
amostradas aleatoriamente, sem controlo por categoria) que `merge-75`, com
uma receita diferente, não sofre. `legal_refusal` também é revelador ao
contrário: `merge-75` (−10,0pp, 1 item em 10) fica *pior* que `legal-v1`
aqui, apesar de ser o checkpoint geral mais "seguro" — o treino específico
de recusa fundamentada do `legal-v1` claramente ajuda nesta categoria
concreta onde `merge-75` não tem qualquer exposição.

## Veredicto: alvo validado com margem larga; três categorias secundárias fora da tolerância estrita

O alvo moveu-se **+66,0pp** — muito além de qualquer erro-padrão razoável
para n=50 (±~5-7pp) — e `legal_refusal` manteve-se no teto (100%), ou seja
o LoRA não trocou grounding por sobre-citação indiscriminada. Confirmado
por leitura direta das respostas: dos 42 itens que falhavam no baseline
por "não usou tag [F#]" apesar de já extrair a informação certa do
contexto, a maioria passou a citar corretamente — exatamente a lacuna de
formato (não de grounding) identificada no baseline antes de treinar.

`honesty` (+28,0pp) é um salto grande, e este projeto já documentou que
saltos de honestidade não explicados devem ser tratados com ceticismo (ver
PILOT-iave-v1.md sobre o salto de +10pp nunca bem explicado). Verificado
por amostragem: dos 36 itens que viraram de falha para sucesso, as
respostas são recusas genuínas e calibradas ("Não conheço o pintor
Casimiro Quintanilha de Sortelha..."), não uma recusa cega — confirmado
pelo facto de `honesty_control` (que pune sobre-recusa em entidades reais)
se manter em 97,2%, quase no teto. Plausível que o próprio treino de
recusa fundamentada do `amalia-cita-legal` (15% dos exemplos-alvo) tenha
reforçado a disciplina geral de "admite quando não sabes" para além do
domínio jurídico.

A regra de aceitação estrita ("harness pt-PT sobe; outras categorias não
descem mais de 1-2pp") falha em três pontos: `variety` (−3,4pp),
`honesty_control` (−2,8pp) e `mcq` (−2,7pp) — todos fora da banda 1-2pp,
mas todos dentro da margem de um único item a mais (n=30/36/37 → 1 item =
2,7-3,4pp). ~~`mcq` é a mais interessante das três... um sinal real de
interferência cruzada entre domínios especializados~~ — **corrigido acima
após comparar com `merge-75`**: o mesmo −2,7pp aparece lá também, num
checkpoint sem qualquer exposição a direito ou exames, portanto não é
interferência específica de `legal-v1`. `variety` é que mostra divergência
real de `merge-75` (que melhora +6,6pp na mesma categoria) — esse é o sinal
que vale investigar, não `mcq`.

**Precedente direto no próprio projeto:** iave-v2 teve exatamente este
padrão — `format`/`variety` fora da tolerância, `honesty_control` na
margem com "um único item em 36" — e foi classificado "MELHOR, mas ainda
não passa a regra de aceitação estrita", não um "aceite" limpo. `legal-v1`
segue o mesmo padrão nas categorias secundárias, mas com um efeito no alvo
mais de dez vezes maior (+66,0pp vs. +5,4pp) — a hipótese RAG-first (a
lacuna era de formato, não de conhecimento) sai claramente validada,
mesmo sem um "aceite" limpo em todas as categorias.

## Nota de poder estatístico

`legal_cita` (n=50): a diferença observada (+66,0pp) está muito acima de
qualquer erro-padrão plausível — resultado robusto, não ruído. `variety`
(n=30), `honesty_control` (n=36) e `mcq` (n=37): cada "regressão" reportada
corresponde a exatamente 1 item a mais/menos a falhar — reais o suficiente
para anotar, pequenas demais para tratar qualquer uma como definitivamente
resolvida ou por resolver.

## Próximos passos (se prosseguir)

1. Recuperar `variety` especificamente (não `mcq`, que é ruído genérico de
   *drift* partilhado até por `merge-75`) — testar se um mix com âncoras
   estratificadas por categoria (não amostradas aleatoriamente de
   `mix-v4`, a mesma lacuna identificada no PILOT-iave-v2.md e nunca
   corrigida) fecha a divergência de +6,6pp vs. `legal-v1`'s −3,4pp sem
   perder o ganho em `legal_cita`.
2. O `legal_cita` do baseline (16,0%) já mostrava que o modelo extraía a
   informação certa mas não citava — o ganho de +66,0pp confirma que isto
   era mesmo um problema de formato treinável a pequena escala. Não há
   sinal aqui de que seja necessário escalar para o corpus completo
   (~9K exemplos) para validar a hipótese; escalar faria sentido para
   robustecer a margem nas categorias secundárias, não para "desbloquear"
   o alvo.
3. Corrigir o teto de memória em falta no caminho de treino do
   `mlx_lm.lora` (replicar `mx.set_memory_limit`/`set_wired_limit` de
   `run_harness.py`) antes do próximo piloto, em vez de confiar num
   smoke-test manual de cada vez.
