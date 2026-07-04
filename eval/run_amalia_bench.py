"""Run AMALIA-Bench tasks on a Mac via MLX + lm-evaluation-harness.

The consortium's amalia-lm-eval repo pins CUDA/vllm, but its tasks are standard
lm-eval YAML — this wrapper loads them with include_path and runs them against
an MLX model (mlx_lm.evaluate's MLXLM bridge).

Usage:
  python eval/run_amalia_bench.py --model amalia-llm/AMALIA-9B-0626-DPO \
      --tasks calame_pt_handwritten ifeval_mt_pt --limit 30 --label baseline
"""

import argparse
import json
from pathlib import Path

import os

import mlx.core as mx

try:
    mx.set_memory_limit(int(os.environ.get("EVAL_MEM_GB", "24")) * 1024**3)
    mx.set_wired_limit(int(os.environ.get("EVAL_WIRED_GB", "20")) * 1024**3)
    # bound the Metal buffer cache: long generation loops otherwise accumulate
    # freed buffers until the wired ceiling and die with a Metal OOM
    mx.set_cache_limit(int(os.environ.get("EVAL_CACHE_GB", "3")) * 1024**3)
except Exception:
    pass

import lm_eval
from lm_eval.tasks import TaskManager
from mlx_lm.evaluate import MLXLM

TASKS_DIR = Path(__file__).parent.parent / "amalia-lm-eval" / "tasks" / "amalia-bench"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tasks", nargs="+", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--num-fewshot", type=int, default=None)
    ap.add_argument("--label", required=True)
    ap.add_argument("--batch-size", type=int, default=8)
    args = ap.parse_args()

    tm = TaskManager(include_path=str(TASKS_DIR))
    lm = MLXLM(args.model, batch_size=args.batch_size, use_chat_template=True)

    results = lm_eval.simple_evaluate(
        model=lm,
        tasks=args.tasks,
        task_manager=tm,
        limit=args.limit,
        num_fewshot=args.num_fewshot,
        apply_chat_template=True,
        confirm_run_unsafe_code=True,
    )

    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"amalia-bench-{args.label}.json"
    slim = {
        "label": args.label,
        "model": args.model,
        "limit": args.limit,
        "results": results["results"],
        "versions": results.get("versions", {}),
        "n-samples": results.get("n-samples", {}),
    }
    with open(out, "w") as f:
        json.dump(slim, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps(slim["results"], ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
