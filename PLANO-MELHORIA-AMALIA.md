# Plano — Melhorar o AMALIA-9B (pt-PT)

Objetivo: atacar os modos de falha observados (aritmética, instruction-following, autoverificação falsa, deslizes pt-BR) via dados de SFT/DPO verificáveis, medindo progresso sem regressão. Iterar barato no Mac; gastar GPU só quando o dataset provar valor.

---

## Fase 0 — MacBook M5 Pro 48GB (custo €0, começa já)

**1. Correr o modelo real**
- AMALIA-9B em BF16 (~18GB, cabe nos 48GB): `mlx_lm.chat --model amalia-llm/AMALIA-9B-0626-DPO`

**2. Montar a avaliação (a peça mais valiosa)**
- **Harness pt-PT próprio (mede progresso):** prompts com restrições verificáveis por código — tempos que somam N, cotações que somam 100, tratamento por "tu", contagem de itens — + detetores de pt-BR (você, celular, gerúndios) e verificação aritmética.
- **Bateria internacional (mede não-regressão):**
  - IFEval — instruções verificáveis (o gémeo internacional do harness)
  - Global-MMLU (subset pt) — conhecimento geral, canário do esquecimento catastrófico
  - GSM8K (tradução pt) — raciocínio aritmético
  - FLORES-200 en↔pt — tradução (força da base EuroLLM; se cair, há dano)
  - CALAME-PT — um dos raros benchmarks de português europeu
- Usar o **amalia-lm-eval** (fork de avaliação do consórcio) para números comparáveis com o technical report.
- **Baseline:** correr tudo no modelo original antes de qualquer treino.

**3. Dataset piloto (alguns milhares de exemplos)**
- Teacher self-hosted no Mac, quantizado 4-bit: EuroLLM-22B-Instruct (coerência soberanista) ou Mistral Small.
- Nunca Claude/GPT: os ToS proíbem treinar modelos com os outputs — vício jurídico num dataset Apache 2.0.
- Pipeline: gerar prompts com restrições verificáveis → amostrar N respostas do teacher → filtrar com os verificadores do harness → aprovados = SFT; rejeitados = negativos para DPO.
- **Descontaminar:** garantir que o dataset não contém itens dos benchmarks.

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

## Fase 2 — Abrir e escalar

**8. Publicar** dataset + harness + checkpoint no HF (Apache 2.0); apresentar resultados ao consórcio AMALIA com números do amalia-lm-eval.

**9. Escalar se justificar:**
- Compute gratuito: candidatura FCT/EuroHPC (Deucalion, MareNostrum5).
- Ou nó alugado 8× H100: SFT focado ~€500-1.500; ciclo completo SFT+DPO ~€3-15k.
- Quando a base migrar para EuroLLM-22B (fase 2 do consórcio), repetir a receita — o dataset e o harness reaproveitam-se por inteiro.

---

## Referência rápida de hardware

| Ação | Onde | Nota |
|---|---|---|
| Inferência 9B BF16 | Mac 48GB | cabe (~18GB) |
| LoRA 9B | Mac 48GB | mlx_lm.lora |
| Full SFT 9B | 2× RTX 6000 Ada | com 8-bit optimizer + FSDP; 2-4 dias |
| Full SFT confortável | 8× H100 (nó) | horas; ~€2-3/GPU-h |
| DPO 9B | 2× RTX 6000 Ada | ref logprobs pré-computados |
| Base 22B | EuroHPC / nó alugado | quando existir AMALIA-22B |
