"""Build the pilot-v4 mix: BOTH anchor styles with matched instructions.

The v2+v3 ablation showed anchor style transfers to task style: bare answers
protect answer-only arithmetic (v2, +3pp), short-reasoning answers boost
CoT-style tasks (v3, GSM8K +16pp) while damaging answer-only (−13pp). v4
trains on both, each paired with the instruction that requests it:

  refusals        200  collision-free resampling (v3 pools)
  real_qa+boundary ~242 reused from the v3 on-policy cache
  arith_bare      ~170 "Responde apenas com…" → bare answer (shards 300+302)
  arith_reasoned  ~143 "Explica numa linha…" → short reasoning (v3 cache)
  format           ~78 shard 301, eval-filtered

Training cap: 200 iters (v3 sweep showed late-training collapse at 300).

Requires shard 302 (bare arithmetic):
  python -m datagen.worker --role draft --backend mlx \
      --model mlx-community/Ministral-3-14B-Reasoning-2512-4bit \
      --shard 302 --num-shards 1 --per-category 120 --categories arithmetic

Usage: python -m datagen.build_mix_v4   (no model loading — runs in seconds)
"""

import json
import random
from pathlib import Path

from datagen.build_mix_v3 import build_refusals, clean, load_eval_prompts


def shard_rows(here, shard, category, eval_prompts, cap):
    rows = []
    for f in (here / "out").glob(f"shard-{shard:03d}-draft-*.jsonl"):
        for line in open(f):
            r = json.loads(line)
            if (r["category"] == category and r["verifier"]["passed"]
                    and r["prompt"] not in eval_prompts and len(rows) < cap):
                rows.append({"messages": [{"role": "user", "content": r["prompt"]},
                                          {"role": "assistant", "content": r["final"]}],
                             "slice": f"{category}_bare" if category == "arithmetic" else category})
    return rows


def cached_rows(here, name, eval_prompts):
    cache = here / "mix-v3" / "slices" / f"{name}.jsonl"
    return clean([json.loads(l) for l in open(cache)], eval_prompts)


def main():
    here = Path(__file__).parent
    rng = random.Random(7400)
    eval_prompts = load_eval_prompts(here)

    rows, seed = [], 7400
    while len(rows) < 200:
        batch = clean(build_refusals(80, random.Random(seed)), eval_prompts)
        existing = {r["messages"][0]["content"] for r in rows}
        rows += [b for b in batch if b["messages"][0]["content"] not in existing][:200 - len(rows)]
        seed += 1

    rows += cached_rows(here, "onpolicy", eval_prompts)        # real_qa + boundary
    rows += cached_rows(here, "arith_reasoned", eval_prompts)  # reasoning style
    rows += shard_rows(here, 300, "arithmetic", eval_prompts, 80)   # bare style
    rows += shard_rows(here, 302, "arithmetic", eval_prompts, 120)  # bare style
    rows += shard_rows(here, 301, "format", eval_prompts, 100)

    collisions = [r for r in rows if r["messages"][0]["content"] in eval_prompts]
    assert not collisions, f"TRAIN/EVAL COLLISION: {len(collisions)}"

    rng.shuffle(rows)
    n_valid = max(50, len(rows) // 12)
    out = here / "mix-v4"
    out.mkdir(exist_ok=True)
    for name, chunk in [("valid", rows[:n_valid]), ("train", rows[n_valid:])]:
        with open(out / f"{name}.jsonl", "w") as f:
            for r in chunk:
                f.write(json.dumps({"messages": r["messages"]}, ensure_ascii=False) + "\n")
    from collections import Counter
    print("mix-v4:", dict(Counter(r["slice"] for r in rows)),
          f"-> train {len(rows) - n_valid}, valid {n_valid}")


if __name__ == "__main__":
    main()
