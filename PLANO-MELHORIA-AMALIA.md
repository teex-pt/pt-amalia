# Plano — Melhorar o AMALIA-9B (pt-PT)

Objetivo: atacar os modos de falha observados (aritmética, instruction-following, autoverificação falsa, deslizes pt-BR) via dados de SFT/DPO verificáveis, medindo progresso sem regressão. Iterar barato no Mac; gastar GPU só quando o dataset provar valor.

**Estado (2026-07-03):** Fase 0 em curso — harness pt-PT implementado (`harness/`, 120 prompts, verificadores em código, 21 testes); `amalia-lm-eval` do consórcio a correr no Mac via MLX (`eval/`); baseline do modelo original em execução. Pipeline de dados desenhado (ver ponto 3).

---

## Fase 0 — MacBook M5 Pro 48GB (custo €0, começa já)

**1. Correr o modelo real**
- AMALIA-9B em BF16 (~18GB, cabe nos 48GB): `mlx_lm.chat --model amalia-llm/AMALIA-9B-0626-DPO`

**2. Montar a avaliação (a peça mais valiosa)** ✅ implementado em `harness/` e `eval/`
- **Harness pt-PT próprio (mede progresso):** prompts com restrições verificáveis por código — tempos que somam N, cotações que somam 100, tratamento por "tu", contagem de itens — + detetores de pt-BR (você, celular, gerúndios) e verificação aritmética.
- **Bateria internacional (mede não-regressão):**
  - IFEval — instruções verificáveis (o gémeo internacional do harness)
  - Global-MMLU (subset pt) — conhecimento geral, canário do esquecimento catastrófico
  - GSM8K (tradução pt) — raciocínio aritmético
  - FLORES-200 en↔pt — tradução (força da base EuroLLM; se cair, há dano)
  - CALAME-PT — um dos raros benchmarks de português europeu
- Usar o **amalia-lm-eval** (fork de avaliação do consórcio) para números comparáveis com o technical report.
- **Baseline:** correr tudo no modelo original antes de qualquer treino.

**3. Dataset piloto (alguns milhares de exemplos) — pipeline em dois andares**
- **Andar 1 (conteúdo):** teacher forte gera a substância (solução, JSON, resposta); traços de raciocínio `[THINK]` são removidos. Não importa se sai em pt-BR ou inglês — é rascunho.
- **Andar 2 (superfície):** EuroLLM-22B ou o próprio AMALIA reescreve em pt-PT com instrução restrita («mantém exatamente os números, a estrutura e o formato»). Rota alternativa: teacher responde em inglês e o EuroLLM traduz (tradução é a especialidade da base EuroLLM).
- **Verificadores correm sobre o texto FINAL, não sobre o rascunho** — resposta confere com a verdade construída, restrições mantidas, zero marcadores pt-BR. Reescrita má custa rendimento, nunca qualidade.
- **Routing de teachers por categoria** (Apache 2.0 todos; decidir por yield medido nos verificadores, não por fé):
  | Categoria | Teacher | Nota |
  |---|---|---|
  | Aritmética + brevidade | Ministral-3-14B-Reasoning-2512 | reasoning-tuned; ~8GB em 4-bit; resposta conhecida por construção — o teacher só fraseia |
  | Formato / instruction-following | Ministral-3-14B (1.ª tentativa); Mistral Small 3.2 como fallback | medir yield e decidir |
  | Variedade pt-PT / prosa | EuroLLM-22B-Instruct ou AMALIA | fidelidade pt-PT é o critério; Mistral fica fora |
  | Honestidade / anti-confabulação | qualquer | pares em grande parte construídos por template |
- **DPO on-policy:** as respostas diretas do AMALIA que chumbam nos verificadores são os «rejected»; a resposta verificada do pipeline é o «chosen». Corrige erros que o modelo realmente comete.
- **Áreas prioritárias (Tier 1, verificáveis por código):** instruction-following com restrições duras; problemas aritméticos com restrição de brevidade; pureza pt-PT (reescritas pt-BR→pt-PT + geração condicionada); anti-confabulação (entidades fabricadas + eventos futuros). **Tier 2:** QA cultural ancorado em fontes; código (humaneval_pt); tradução en→pt-PT como proteção anti-regressão.
- Nunca Claude/GPT: os ToS proíbem treinar modelos com os outputs — vício jurídico num dataset Apache 2.0. Com o pipeline acima, todos os tokens do dataset são de modelos Apache 2.0.
- **Fontes reais (complemento ao sintético):**
  - **Exames nacionais (IAVE):** matemática com critérios de correção = respostas verificáveis por construção; provas de português = pt-PT canónico. ⚠️ O benchmark `pt_exams` do consórcio usa estes exames — extrair apenas anos/ciclos fora do benchmark e filtrar por sobreposição de n-gramas.
  - **Conteúdo legal (dre.pt, dgsi.pt):** textos oficiais isentos de direito de autor (CDADC); registo formal pt-PT em escala. Descontaminar contra `LegalBenchPT`; anonimizar decisões judiciais (RGPD) antes de redistribuir.
  - **BASE contratos públicos (base.gov.pt):** registo contratual/administrativo pt-PT, dados abertos.
  - **Uso:** QA ancorado (pergunta gerada sobre passagem; verificador = correspondência extrativa com a fonte), sementes de reescrita para a categoria variedade, e problemas de exame como aritmética com verdade dos critérios de correção.
- **Datasets individuais, mistura por receita:** um dataset por categoria/fonte (`amalia-sft-aritmetica`, `-formato`, `-variedade`, `amalia-dpo-honestidade`, `amalia-qa-exames`, `-legal`, `-contratos`, e `amalia-sft-raciocinio-traces` com tokens `<think>` para o Path A), todos com o mesmo esquema JSONL (messages, category, veredicto do verificador, proveniência: template_id/teacher/rewriter/source_url). O treino referencia-os com pesos (receita reproduzível). Vantagens: ablações 1:1 com as categorias do harness (causa-efeito medível), licenciamento/proveniência limpos por repositório, iteração independente, relatório de descontaminação por dataset.
- **Descontaminar:** garantir que o dataset não contém itens dos benchmarks (pt_exams, LegalBenchPT, alba, cultura_viva incluídos).
- **O que a mistura SFT original (0626, ~6,5M amostras) já cobre — e porque ainda assim falha:** instruction-following (~2,1M, Nemotron traduzido/inglês, genérico), matemática (~1,4M), identidade (`Amalia_hardcoded`, 780 amostras ×5 — insuficiente: confabulação medida), linguística pt-PT (`ptpt-linguistics-if`, só 200). O próprio card admite «machine translated content … may contain translation errors or artifacts»; o filtro de qualidade foi um juiz LLM (Gemma-4-31B), não verificação por código. **Ausente da mistura:** exames IAVE, conteúdo legal, contratos públicos, e qualquer dado filtrado por verificadores determinísticos. → A nossa aposta não é volume: é dado pt-PT nativo, pequeno e certificado por código, nas falhas que 6,5M amostras não corrigiram — mais os três corpora reais intocados. O `Amalia_hardcoded` é o gancho de colaboração natural para o pipeline de honestidade.

**4. LoRA piloto no Mac**
- `mlx_lm.lora` sobre o AMALIA-9B com o dataset filtrado.
- Medir antes/depois no harness + bateria internacional.
- **Regra de aceitação (vale para todos os checkpoints):** harness pt-PT sobe; internacionais não descem mais de 1-2 pontos.

## Fase 1 — 2× RTX 6000 Ada 48GB (receita validada)

**5. Escalar geração:** teacher em vLLM → 100-500k exemplos filtrados.

**6. Full SFT do 9B (2-4 dias):**
- Não cabe "à clássica" (~145GB de estados de treino em 96GB totais); cabe com: FSDP/ZeRO-3 + AdamW 8-bit + gradient checkpointing + sequências ≤4k.
- Alternativa mais segura e lenta: ZeRO-3 com offload do otimizador para RAM.

**7. DPO:**
- Pré-computar logprobs do modelo de referência offline (não cabe policy + referência em memória).
- Pares: aprovado/rejeitado da filtragem + pares on-policy.
- Reavaliar com a regra de aceitação.

**7b. Path A — AMALIA «pensante» por destilação (decidido 2026-07-03; extensão da Fase 1)**
- Tokens `<think>`/`</think>` no tokenizer e no chat template (com remoção do bloco de raciocínio no serving).
- Dataset `amalia-sft-raciocinio-traces`: amostrar o Ministral-3-14B-Reasoning (Apache 2.0 — os traces são legalmente utilizáveis) sobre problemas com resposta conhecida por construção; manter apenas traces cuja resposta final passa nos verificadores; renderizar em pt-PT pelo pipeline de dois andares. Alvo: 50–100k traces verificados.
- **Ablação pt-PT vs inglês nos traces:** modelos tendem a raciocinar melhor em inglês; deliberação em português é um diferenciador de soberania — medir o custo/ganho, não assumir.
- Treino: é apenas Full SFT — mesmo hardware e receita da Fase 1 (2× RTX 6000, FSDP + otimizador 8-bit). Nenhuma infraestrutura nova.
- Scoreboard já existente no amalia-lm-eval: `aime_pt`, `math-pt`, `minerva_math_pt`, `bbh_mt`, variantes CoT do GSM8K. A regra de aceitação mantém-se (internacionais não descem >1–2 pontos).

## Fase 2 — Abrir e escalar

**8. Publicar** dataset + harness + checkpoint no HF (Apache 2.0); apresentar resultados ao consórcio AMALIA com números do amalia-lm-eval.

**9. Escalar se justificar:**
- Compute gratuito: candidatura FCT/EuroHPC (Deucalion, MareNostrum5).
- Ou nó alugado 8× H100: SFT focado ~€500-1.500; ciclo completo SFT+DPO ~€3-15k.
- Quando a base migrar para EuroLLM-22B (fase 2 do consórcio), repetir a receita — o dataset e o harness reaproveitam-se por inteiro.

**9b. Path B — RLVR (GRPO) com os verificadores como recompensa (candidatura EuroHPC a preparar)**
- Recompensas determinísticas: correção da resposta + conformidade de formato + **penalização de marcadores pt-BR** + penalização de comprimento excessivo. Anti reward-hacking por construção — os verificadores são código, não juízes LLM.
- Piloto de viabilidade: LoRA-GRPO em 2× RTX 6000 Ada (semanas, sinal barato). Corrida real: nó 8× H100 durante vários dias (€5–15k) ou Deucalion/MareNostrum5 via grant.
- Go/no-go decidido pelos resultados do Path A — a destilação captura a maior parte do ganho a 9B; o RLVR só se justifica se o delta restante compensar o grant.

---

## Referência rápida de hardware

| Ação | Onde | Nota |
|---|---|---|
| Inferência 9B BF16 | Mac 48GB | cabe (~18GB) |
| LoRA 9B | Mac 48GB | mlx_lm.lora |
| Full SFT 9B | 2× RTX 6000 Ada | com 8-bit optimizer + FSDP; 2-4 dias |
| Full SFT confortável | 8× H100 (nó) | horas; ~€2-3/GPU-h |
| DPO 9B | 2× RTX 6000 Ada | ref logprobs pré-computados |
| SFT de traces «think» (Path A) | 2× RTX 6000 Ada | igual ao Full SFT da Fase 1 |
| RLVR GRPO piloto (LoRA) | 2× RTX 6000 Ada | semanas; sinal de viabilidade |
| RLVR GRPO completo (Path B) | 8× H100 / EuroHPC | dias; €5–15k ou grant |
| Base 22B | EuroHPC / nó alugado | quando existir AMALIA-22B |
