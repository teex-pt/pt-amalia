"""legal-v2: same recipe as legal-v1 (datagen/build_legal_v1_mix.py), ~2x
the data volume. legal-v1 validated the RAG-first citation-format
hypothesis at a small controlled scale (+66pp on legal_cita); this scales
up the same mix to use more of the available amalia-cita-legal/
amalia-sum-dre pool and widen the margin, per this project's own
measure-then-scale pattern (iave-v1->v2 scaled ~1.65x, not more, and
scaled iters proportionally rather than jumping straight to the full
corpus).

Anchors are still sampled randomly from mix-v4, same as legal-v1 - mix-v4
turned out not to have a distinct "variety" slice to stratify by (variety
looks like an emergent property of the data being pt-PT throughout, not a
dedicated trainable category), so the anchor-stratification idea from
PILOT-legal-v1.md's next-steps is deferred, not applied here. This run is
about data volume only.

Usage: python -m datagen.build_legal_v2_mix
Writes datagen/legal-v2-mix/{train,valid}.jsonl
"""

import json
import random
from pathlib import Path

from transformers import AutoTokenizer

from datagen.build_mix_v3 import load_eval_prompts
from datagen.build_legal_v1_mix import toklen, sample_under_budget

HERE = Path(__file__).parent
CITA_DIR = HERE / "leis-pt" / "cita-legal"
SUM_DIR = HERE / "leis-pt" / "sum-dre"
V4_DIR = HERE / "mix-v4"
OUT = HERE / "legal-v2-mix"

BASE_MODEL = "amalia-llm/AMALIA-9B-0626-DPO"
MAX_SEQ_LEN = 4096  # same validated-safe cap as legal-v1

N_CITA_GROUNDED = 700
N_CITA_REFUSAL = 100
N_SUM = 400
N_ANCHOR = 800  # mix-v4/train.jsonl only has 751 rows total; all get used
SEED = 73102  # disjoint from legal-v1(73002) and every other seed in this project


def load(path):
    return [json.loads(l) for l in open(path)]


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
    anchors = rng.sample(v4_train, min(N_ANCHOR, len(v4_train)))

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
