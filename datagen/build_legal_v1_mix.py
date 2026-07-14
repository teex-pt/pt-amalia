"""legal-v1: first legal-domain LoRA pilot, mixing teex-pt/amalia-cita-legal
and teex-pt/amalia-sum-dre with diversity anchors from mix-v4 - the same
anchor-mixing correction that fixed iave-v1's homogeneous-collapse failure
(see build_iave_v2_mix.py), applied here as the default from the start
rather than learned the hard way a second time.

A small controlled first pilot, not the full ~9K-example corpus: this
project's own pattern has always been measure-first-then-scale (honesty
v1-v4, iave v1-v2), and this is the first pilot with citation-style
contexts this long, so keep the run small enough to validate the recipe
before committing to a much longer one.

Token-length filtered: an unfiltered sample of cita-legal's up-to-6-excerpt
grounded examples has a long tail (measured p99 ~8K tokens, max ~10.8K)
that would silently truncate under mlx_lm's default 2048 max-seq-length, or
even a raised one. Every row here is checked against the real tokenizer and
capped at MAX_SEQ_LEN, with candidates over budget skipped and backfilled
from the larger source pool rather than truncated mid-content.

Usage: python -m datagen.build_legal_v1_mix
Writes datagen/legal-v1-mix/{train,valid}.jsonl
"""

import json
import random
from pathlib import Path

from transformers import AutoTokenizer

from datagen.build_mix_v3 import load_eval_prompts

HERE = Path(__file__).parent
CITA_DIR = HERE / "leis-pt" / "cita-legal"
SUM_DIR = HERE / "leis-pt" / "sum-dre"
V4_DIR = HERE / "mix-v4"
OUT = HERE / "legal-v1-mix"

BASE_MODEL = "amalia-llm/AMALIA-9B-0626-DPO"
# 6144 crashed training with a Metal OOM at iter 3 (peak mem 25.2GB and
# climbing, no ceiling on the mlx_lm.lora training path unlike
# run_harness.py's inference path). Dropped to 4096 + batch-size 1 +
# --grad-checkpoint at train time instead of guessing at a single fix.
MAX_SEQ_LEN = 4096  # must match/exceed --max-seq-length at train time

N_CITA_GROUNDED = 350
N_CITA_REFUSAL = 50
N_SUM = 200
N_ANCHOR = 400
SEED = 73002  # disjoint from harness(42), smoke(7), iave mix(9001/51015), legal eval(73001)


def load(path):
    return [json.loads(l) for l in open(path)]


def toklen(tokenizer, messages):
    """apply_chat_template returns a BatchEncoding here (not a bare list,
    and NOT a dict subclass - isinstance(out, dict) is False for it, a
    trap that silently measured 2 (dict keys) instead of the real token
    count the first time this was written). Index ['input_ids'] instead
    of trusting a dict/list type check."""
    out = tokenizer.apply_chat_template(messages, add_generation_prompt=False)
    ids = out["input_ids"] if hasattr(out, "keys") else out
    return len(ids)


def sample_under_budget(rng, pool, n, tokenizer, max_len):
    """Sample n rows whose tokenized chat-template length is <= max_len,
    backfilling from the pool instead of truncating over-budget rows."""
    order = list(range(len(pool)))
    rng.shuffle(order)
    picked, skipped = [], 0
    for i in order:
        if len(picked) >= n:
            break
        r = pool[i]
        if toklen(tokenizer, r["messages"]) > max_len:
            skipped += 1
            continue
        picked.append(r)
    return picked, skipped


def main():
    cita_train = load(CITA_DIR / "train.jsonl")
    sum_train = load(SUM_DIR / "train.jsonl")
    v4_train = load(V4_DIR / "train.jsonl")

    grounded = [r for r in cita_train if r["label"] == "grounded"]
    refusal = [r for r in cita_train if r["label"] == "refusal"]

    rng = random.Random(SEED)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    picked_grounded, skip_g = sample_under_budget(rng, grounded, N_CITA_GROUNDED, tokenizer, MAX_SEQ_LEN)
    picked_refusal, skip_r = sample_under_budget(rng, refusal, N_CITA_REFUSAL, tokenizer, MAX_SEQ_LEN)
    picked_sum, skip_s = sample_under_budget(rng, sum_train, N_SUM, tokenizer, MAX_SEQ_LEN)
    anchors = rng.sample(v4_train, min(N_ANCHOR, len(v4_train)))  # mix-v4 anchors are already short

    print(f"skipped over {MAX_SEQ_LEN} tokens (backfilled): grounded={skip_g}, "
          f"refusal={skip_r}, sum-dre={skip_s}")

    legal_rows = [{"messages": r["messages"]} for r in picked_grounded + picked_refusal + picked_sum]
    anchor_rows = [{"messages": r["messages"]} for r in anchors]

    eval_prompts = load_eval_prompts(HERE)
    all_rows = legal_rows + anchor_rows
    collisions = [r for r in all_rows if r["messages"][0]["content"] in eval_prompts]
    assert not collisions, f"{len(collisions)} rows collide with a harness eval prompt"

    rng.shuffle(all_rows)
    n_valid = max(50, len(all_rows) // 12)
    valid_rows, train_rows = all_rows[:n_valid], all_rows[n_valid:]

    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in [("train", train_rows), ("valid", valid_rows)]:
        with open(OUT / f"{name}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"legal: {len(picked_grounded)} grounded + {len(picked_refusal)} refusal + "
          f"{len(picked_sum)} sum-dre = {len(legal_rows)}; anchors: {len(anchor_rows)}; "
          f"total {len(all_rows)}")
    print(f"train: {len(train_rows)}, valid: {len(valid_rows)}")


if __name__ == "__main__":
    main()
