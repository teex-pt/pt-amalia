## Summary field (one-line tagline, shown at top of the page and in search listings)

The first fully open large language model built natively for European Portuguese (pt-PT) — quantized and benchmarked by teex for fast local inference.

Shorter alternative if there's a length limit: "Native European Portuguese (pt-PT) LLM, fully open — quantized and benchmarked by teex."

---

## Readme field (full page body, paste separately below the summary)

AMALIA-9B is a fully open, 9-billion-parameter large language model built specifically for **European Portuguese (pt-PT)** — not a translation or fine-tune of an English model, but a model whose pretraining and post-training prioritized native pt-PT data and culture from the ground up. Released 1 July 2026 by a Portuguese academic consortium (NOVA, IST, Fundação para a Ciência e Tecnologia) under the Apache 2.0 license, it is llama-architecture, EuroLLM-based, with a 32K context window.

This repo packages AMALIA-9B for Ollama in four variants, quantized and benchmarked by teex:

- `bf16` (18GB) — the original, full-precision weights, unmodified
- `q8_0` (9.7GB) — near-lossless quality, recommended when fidelity matters most
- `q4_K_M` (5.6GB) / `latest` — fastest, smallest footprint, small but real quality cost
- All variants embed a corrected default system prompt: without one, the base model invents its own identity and biography — these builds instead present it with a factual, non-confabulating self-description

## Benchmarks (measured by teex on an Apple M5 Pro, 48GB)

| Metric | BF16 (original) | Q8_0 | Q4_K_M |
|---|---|---|---|
| Perplexity (pt-PT text, vs BF16) | — (reference) | −0.1% (noise — effectively lossless) | +2.7% |
| Generation speed | ~16 tok/s | ~30 tok/s | ~48 tok/s |

Full methodology, raw benchmark data, and a pt-PT evaluation harness (arithmetic, instruction-following, honesty/anti-confabulation, pt-PT vs pt-BR variety) are open source: [github.com/teex-pt/pt-amalia](https://github.com/teex-pt/pt-amalia).

## Use cases

Prompt in European Portuguese — that's what the model is tuned for, and what it does best: conversational Portuguese, cultural and historical Q&A, translation into/out of pt-PT, and general instruction-following. It is not a coding or heavy-math specialist model.

## Attribution

All credit for the model itself goes to the [AMALIA project](https://amalia-llm.github.io/intro.html) and its consortium. This repo is a quantization, benchmarking, and Ollama-packaging contribution by teex — not the model's original authors. Base model: [amalia-llm/AMALIA-9B-0626-DPO](https://huggingface.co/amalia-llm/AMALIA-9B-0626-DPO) (Apache 2.0).
