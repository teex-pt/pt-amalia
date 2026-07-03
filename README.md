# pt-amalia

Quantization, benchmarking and findings for **AMALIA-9B** — the Portuguese (pt-PT) 9B open-source LLM presented on 1 July 2026 — plus an improvement plan for its observed failure modes.

We published the first Apple Silicon (MLX) and cross-platform (GGUF) builds of the model, each with a findings-driven model card:

| Repo | What | For |
|---|---|---|
| [teex-pt/AMALIA-9B-0626-DPO-MLX-8bit](https://huggingface.co/teex-pt/AMALIA-9B-0626-DPO-MLX-8bit) | MLX 8-bit (9.1 GB) | Macs — near-lossless, 30 tok/s on M5 Pro |
| [teex-pt/AMALIA-9B-0626-DPO-MLX-4bit](https://huggingface.co/teex-pt/AMALIA-9B-0626-DPO-MLX-4bit) | MLX 4-bit (4.8 GB) | Macs — fastest, 55+ tok/s |
| [teex-pt/AMALIA-9B-0626-DPO-GGUF](https://huggingface.co/teex-pt/AMALIA-9B-0626-DPO-GGUF) | GGUF Q4_K_M + Q8_0 | everyone — Ollama, LM Studio, llama.cpp, any OS/GPU |

## Findings (summary)

Measured on an Apple M5 Pro 48 GB (mlx-lm 0.31.3, llama.cpp b9850), greedy decoding, fixed pt-PT prompts:

1. **8-bit quantization is free** — perplexity within noise of BF16 in both runtimes; outputs near-identical.
2. **4-bit is cheap but not free** — +2.7% (GGUF Q4_K_M) to +4.3% (MLX RTN) perplexity; occasional factual slips (hallucinated Camões attributions, an English word leaking into pt-PT JSON).
3. **K-quants beat round-to-nearest at 4-bit** — same size, measurably less damage.
4. **Speed tracks bytes, not runtime** — MLX and llama.cpp are equally fast at equal bit-width on Apple Silicon (BF16 ≈ 16 tok/s → Q8 ≈ 30 → Q4 ≈ 48–59).
5. **Identity confabulation** — without a system prompt the model invents personas and origins; our builds embed a factual default presentation prompt (see `new-chat-template.jinja`), fully overridable.

Raw data: `bench-*.json` / `bench-*.md` (three MLX variants, reproducible with `bench.py`).

## Contents

- `bench.py` — deterministic benchmark suite for any MLX build (speed, memory, perplexity, fixed pt-PT prompts, long-context needle)
- `gguf-pipeline.sh` — HF safetensors → BF16 GGUF → Q4_K_M/Q8_0 + validation
- `new-chat-template.jinja` — chat template with the factual default system prompt (minja- and jinja2-compatible)
- `bench-{bf16,q8,q4}.{json,md}` — benchmark results
- `PLANO-MELHORIA-AMALIA.md` — improvement plan: pt-PT eval harness, verifiable SFT/DPO data, LoRA pilot → GPU scale-up

## Reproducing

```bash
python3 -m venv .venv && .venv/bin/pip install mlx-lm
.venv/bin/mlx_lm.convert --hf-path amalia-llm/AMALIA-9B-0626-DPO -q --q-bits 8 --mlx-path amalia-mlx-8bit
.venv/bin/python bench.py --model ./amalia-mlx-8bit --label q8
zsh gguf-pipeline.sh   # GGUF conversion + validation
```

## Attribution & license

All credit for the model goes to the [AMALIA team](https://amalia-llm.github.io/intro.html); original model [amalia-llm/AMALIA-9B-0626-DPO](https://huggingface.co/amalia-llm/AMALIA-9B-0626-DPO) (Apache 2.0). This repo: Apache 2.0.
