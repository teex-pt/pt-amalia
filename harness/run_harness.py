"""Run the pt-PT harness against an MLX model and score with code verifiers.

Usage (from the repository root):
    python -m harness.run_harness --model <hf-repo-or-path> --label baseline

Writes harness/results-<label>.jsonl (per-item responses and verdicts) and
harness/summary-<label>.json (per-category pass rates). Greedy decoding —
fully reproducible.
"""

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import mlx.core as mx

try:
    mx.set_memory_limit(24 * 1024**3)
    mx.set_wired_limit(20 * 1024**3)
except Exception:
    pass

from mlx_lm import load, stream_generate

from harness.verifiers import CHECKERS

MAX_TOKENS = {"arithmetic": 60, "format": 300, "variety": 120, "honesty": 150,
              "honesty_control": 150, "mcq": 40}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--limit", type=int, default=0, help="per-category cap, 0 = all")
    ap.add_argument("--prompts-file", default="prompts.jsonl",
                    help="prompts file inside harness/ (e.g. control_prompts.jsonl)")
    ap.add_argument("--adapter-path", default=None, help="LoRA adapter directory")
    args = ap.parse_args()

    here = Path(__file__).parent
    items = [json.loads(l) for l in open(here / args.prompts_file)]
    if args.limit:
        by_cat = defaultdict(list)
        for i in items:
            if len(by_cat[i["category"]]) < args.limit:
                by_cat[i["category"]].append(i)
        items = [i for cat in by_cat.values() for i in cat]

    model, tokenizer = load(args.model, adapter_path=args.adapter_path)
    t0 = time.time()
    results, tally = [], defaultdict(lambda: [0, 0])

    for n, item in enumerate(items, 1):
        ids = tokenizer.apply_chat_template(
            [{"role": "user", "content": item["prompt"]}], add_generation_prompt=True)
        text = ""
        for r in stream_generate(model, tokenizer, ids,
                                 max_tokens=MAX_TOKENS[item["category"]]):
            text += r.text
        mx.clear_cache()
        passed, reason = CHECKERS[item["category"]](item, text.strip())
        tally[item["category"]][0] += passed
        tally[item["category"]][1] += 1
        results.append({**item, "response": text.strip(), "passed": passed, "reason": reason})
        if n % 10 == 0:
            print(f"{n}/{len(items)} done ({time.time() - t0:.0f}s)", flush=True)

    with open(here / f"results-{args.label}.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "label": args.label, "model": args.model,
        "categories": {c: {"passed": p, "total": t, "rate": round(p / t, 3)}
                       for c, (p, t) in sorted(tally.items())},
    }
    summary["overall"] = round(sum(p for p, _ in tally.values()) / len(results), 3)
    with open(here / f"summary-{args.label}.json", "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
