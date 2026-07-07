# Piloto LoRA iave-v1 — especialização K-12/IAVE (2026-07-07)

Primeiro ciclo do corpus IAVE (452→425 amostras após reserva do conjunto de
avaliação): gerar dataset verificado → treinar → medir contra o baseline e o
novo conjunto `harness/iave_prompts.jsonl` (37 itens, 11 disciplinas,
disjunto por sessão de exame, não apenas por linha).

- **Dataset:** 383 train + 42 valid, todas amostras MCQ do IAVE (2024-2025),
  schema `messages` padrão do projeto, único e homogéneo (só perguntas de
  escolha múltipla, mesmo template de prompt em todas).
- **Treino:** `mlx_lm.lora`, base BF16, 200 iters, batch 2, 16 camadas, lr 1e-5,
  ~21,3 GB pico, ~4,5 min. Train loss 2,206→0,843; val loss 6,542→0,858 (sem
  sinais de divergência). Adapter em `adapters/iave-v1/` (não versionado).

## Resultados

| Categoria | Baseline | LoRA iave-v1 | Δ |
|---|---|---|---|
| **mcq (IAVE, o alvo)** | 29,7% (11/37) | **29,7% (11/37)** | **0,0pp** ❌ |
| arithmetic | 46,0% | 42,0% | **−4,0pp** ❌ |
| format | 73,3% | 66,7% | **−6,6pp** ❌ |
| variety | 86,7% | 83,3% | **−3,4pp** ❌ |
| honesty | 50,0% | **60,0%** | +10,0pp ✅ (não intencional) |
| controlo (honesty_control, 36 itens) | 100% | 97,2% (35/36) | −2,8pp ❌ (fora da tolerância, marginal) |
| overall (extended, 260 itens) | 55,4% | 56,5% | +1,1pp (média enganadora) |

## Veredicto: CHECKPOINT REJEITADO (regra de aceitação)

A regra ("harness pt-PT sobe; internacionais/controlo não descem mais de
1-2pp") falha em dois eixos independentes:

1. **A métrica-alvo não mexeu.** 0,0pp em `mcq` — o objetivo inteiro deste
   piloto (melhorar desempenho em exames) não foi alcançado, apesar do
   treino ser inteiramente sobre dados de exames IAVE. Nota de poder
   estatístico: n=37 tem um erro-padrão de ±~7,5pp, portanto isto não prova
   que o skill é inaprendível — só que este piloto não produziu sinal
   detetável.
2. **Interferência noutras categorias, acima da tolerância.** arithmetic
   −4,0pp, format −6,6pp, variety −3,4pp, controlo −2,8pp. Quatro categorias
   independentes a regredir aponta para um padrão sistemático, não ruído.

**Verificação de que o adapter estava mesmo a aplicar-se** (não foi um erro
de carregamento): comparei respostas item-a-item baseline vs. piloto no
conjunto `mcq` — 28/29 respostas mudaram de texto. O piloto aprendeu
claramente a convenção de formato exata do treino (`"(X)"` em vez de `"X"`
solto), mas isso não se traduziu em mais respostas corretas.

## Diagnóstico: repetição do erro do piloto honesty-v1

Este é essencialmente o **mesmo padrão de falha do honesty-v1** (2026-07-04,
ver acima): treino de **vetor único, sem âncoras de diversidade**. O mix
IAVE é 100% MCQ — mesmíssimo template de prompt (`"[Exame Nacional de...]
... Qual é a opção correta? Responde apenas com a letra."`) em todas as 383
amostras, sem nenhuma amostra de aritmética livre, formato JSON, ou QA
aberto misturada. Um LoRA rank-8/16-camadas sobre um conjunto tão homogéneo
tem espaço de sobra para aprender "responde sempre com uma letra entre
parênteses, sê breve" como padrão dominante — e esse padrão de brevidade
extrema vaza para arithmetic/format/variety, que não pedem esse estilo.

A honesty-v1→v2 já validou a correção exata para isto neste mesmo projeto:
misturar âncoras de outras categorias junto com o vetor-alvo. Não foi feito
aqui porque o objetivo imediato era medir o corpus IAVE isoladamente
(pergunta em aberto: "este corpus, sozinho, move a agulha?" — resposta:
não, pelo menos não a esta escala).

## Porque é que `mcq` não moveu, especificamente

383 exemplos espalhados por ~24 disciplinas (excluindo as 11 reservadas para
avaliação) dão uma média de ~16 exemplos por disciplina — provavelmente
insuficiente para um modelo de 9B aprender conhecimento de domínio novo por
disciplina em 200 iterações, mesmo que seja mais do que suficiente para
aprender a convenção de formato de saída (um padrão sintático simples e
uniforme, não conhecimento factual disperso).

## Receita v2 (próxima iteração, se prosseguir)

- **Misturar âncoras**, replicando a correção honesty-v1→v2: amostras de
  `mix-v4` (aritmética, formato, variedade) lado a lado com o IAVE MCQ, não
  IAVE isolado.
- **Mais iterações e/ou mais dados por disciplina** antes de concluir que o
  skill é inatingível a esta escala — o resultado atual (n=37) não tem poder
  estatístico para distinguir "não aprendeu" de "aprendeu pouco, ruído
  esconde".
- Considerar se **RAG/retrieval sobre o corpus** (em vez de fine-tuning
  paramétrico) não é a abordagem mais eficaz para conhecimento factual denso
  como conteúdo de exames — mesma conclusão a que chegámos independentemente
  ao planear o projeto leis-pt no mesmo dia.

## Leitura estratégica

Resultado negativo, mas informativo e barato (~5 minutos de treino + ~5
minutos de avaliação no total). Confirma, com um segundo exemplo
independente no mesmo projeto, que **fine-tuning de vetor único sem
âncoras de diversidade é um erro sistemático, não um acidente do piloto
honesty-v1** — vale a pena tornar isto uma regra permanente do pipeline
(nunca treinar um LoRA só com um tipo de amostra), não só uma lição
pontual.
