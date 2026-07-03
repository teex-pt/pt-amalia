# datagen — distributed synthetic dataset generation

Generation is embarrassingly parallel: workers on different machines each take
a deterministic shard of seeded templates, draft with a local model, verify
with the code verifiers, and write a self-contained JSONL shard. No
coordination during generation; shards merge centrally afterwards.

## Fleet layout (example: 3 heterogeneous machines)

| Machine | Backend | Model | Role |
|---|---|---|---|
| MacBook M5 Pro 48 GB | `mlx` | Ministral-3-14B-Reasoning-4bit / Mistral-Small-3.2-4bit / EuroLLM-22B-4bit | `draft` (arithmetic+format) + rewrite queue |
| MacBook M1 16 GB | `mlx` | Ministral-3-14B-Reasoning-4bit (~8 GB) | `draft`, its own shard |
| Ryzen + RTX 4060 Ti 16 GB | `api` | [teex-pt/AMALIA-9B-0626-DPO-GGUF](https://huggingface.co/teex-pt/AMALIA-9B-0626-DPO-GGUF) via `llama-server` | `onpolicy` (honesty/variety — DPO negatives must come from the student) |

## Setup per machine

Macs: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` in a
clone of this repo. CUDA/CPU box: any OpenAI-compatible server works, e.g.

```bash
llama-server -m AMALIA-9B-0626-DPO-Q4_K_M.gguf --port 8080 -ngl 99
```

## Run

```bash
# shard i of N on each machine (different --shard per machine/run):
python -m datagen.worker --role draft --backend mlx \
    --model mlx-community/Ministral-3-14B-Reasoning-2512-4bit \
    --shard 0 --num-shards 4 --per-category 50

python -m datagen.worker --role onpolicy --backend api \
    --api-base http://localhost:8080/v1 --model amalia \
    --shard 2 --num-shards 4 --per-category 50
```

Shards land in `datagen/out/shard-*.jsonl`. Collect them onto one machine
(rsync/scp, or push to a private HF dataset repo) and merge:

```bash
python -m datagen.merge_shards
```

This re-verifies every sample with the current verifier version, deduplicates,
and writes `merged/sft.jsonl`, `merged/dpo.jsonl`, `merged/rewrite_queue.jsonl`
plus a per-category/per-host yield report (`merged/stats.json`).

## Invariants

- Ground truth is computed by the templates, never by a model.
- Verifiers gate the final text; the merge step re-verifies everything centrally.
- Honesty items are always answered by AMALIA itself (on-policy DPO).
- Shard seeds (1000+shard) never overlap the harness (seed 42) or the smoke
  sample (seed 7); decontamination against published benchmarks happens before
  any dataset release.
