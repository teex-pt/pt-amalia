# Fase 0 — Baseline do modelo original (antes de qualquer treino)

- **Modelo:** `amalia-llm/AMALIA-9B-0626-DPO` (BF16, template de chat original, greedy)
- **Data:** 2026-07-03 · **Hardware:** Apple M5 Pro 48 GB (MLX)
- **Regra de aceitação para futuros checkpoints:** harness pt-PT sobe; benchmarks internacionais não descem mais de 1–2 pontos face a esta tabela.

## Harness pt-PT próprio (120 prompts, verificadores em código)

| Categoria | Pass rate | Interpretação |
|---|---|---|
| **honesty** (anti-confabulação) | **43,3%** (13/30) | pior categoria — confirma a confabulação de identidade/factos medida qualitativamente |
| **arithmetic** (+ brevidade) | **60,0%** (18/30) | erros de cálculo e violações de brevidade |
| **format** (restrições duras) | **73,3%** (22/30) | consistente com o IFEval-pt abaixo |
| **variety** (pt-PT vs pt-BR) | **86,7%** (26/30) | melhor categoria — o pt-PT é a força do modelo |
| **Overall** | **65,8%** | |

Reproduzir: `python -m harness.run_harness --model amalia-llm/AMALIA-9B-0626-DPO --label <label>`
Respostas por item: `harness/results-baseline-bf16.jsonl`.

## AMALIA-Bench (amostras limitadas — smoke baseline)

| Tarefa | n | Métrica | Valor |
|---|---|---|---|
| `ifeval-mt-pt` | 25 | prompt-level strict acc | **60,0%** |
| `ifeval-mt-pt` | 25 | inst-level strict acc | **73,0%** |
| `calame_pt_handwritten` | 50 | exact match | **20,0%** ⚠️ |
| `amalia_gsm8k_cot_zeroshot_mt_pt` | 25 | exact match | _(a correr — preencher quando terminar)_ |

⚠️ **Caveat CALAME:** corrido com template de chat aplicado; o CALAME é uma tarefa de *completação* (prever a última palavra) e o consórcio avalia-o provavelmente sem template. O valor não é comparável com o technical report — serve apenas como referência interna antes/depois com o mesmo protocolo. Para números comparáveis com o consórcio, correr sem `--apply-chat-template` (e idealmente no setup vLLM deles).

**Nota geral:** amostras limitadas (25–50) para o smoke baseline no Mac — os intervalos de confiança são largos (±10pp no IFEval). Antes do primeiro LoRA, correr as tarefas completas overnight para apertar o baseline.

## Leitura estratégica

A ordenação das categorias do harness coincide com a análise qualitativa e com as lacunas da mistura SFT original: honestidade (43%) e aritmética-com-brevidade (60%) são exatamente as áreas onde a mistura de 6,5M amostras não tem dados verificados — e são as duas primeiras prioridades do pipeline sintético (plano, ponto 3).
