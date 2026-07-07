"""iave-v2: fix iave-v1's rejection by mixing in diversity anchors, the same
correction that fixed honesty-v1 (single-vector SFT, zero diversity anchors,
narrow response style leaked into unrelated categories - see
eval/results/PILOT-iave-v1.md).

Keeps all of datagen/iave/mix/{train,valid}.jsonl (the actual target skill)
and adds a random sample from datagen/mix-v4/{train,valid}.jsonl (already a
validated, diverse mix: arithmetic, format, variety, honesty, on-policy QA,
reasoning traces) as anchors - roughly the same ~60/40 target/anchor ratio
honesty-v2 used to fix the analogous problem.

Usage: python -m datagen.build_iave_v2_mix
Writes datagen/iave-v2-mix/{train,valid}.jsonl
"""

import json
import random
from pathlib import Path

IAVE_DIR = Path(__file__).parent / "iave" / "mix"
V4_DIR = Path(__file__).parent / "mix-v4"
OUT = Path(__file__).parent / "iave-v2-mix"

N_ANCHOR_TRAIN = 250
N_ANCHOR_VALID = 20
SEED = 51015  # disjoint from harness(42), smoke(7), iave mix(9001), v4's own seed


def load(path):
    return [json.loads(l) for l in open(path)]


def main():
    iave_train = load(IAVE_DIR / "train.jsonl")
    iave_valid = load(IAVE_DIR / "valid.jsonl")
    v4_train = load(V4_DIR / "train.jsonl")
    v4_valid = load(V4_DIR / "valid.jsonl")

    rng = random.Random(SEED)
    anchor_train = rng.sample(v4_train, N_ANCHOR_TRAIN)
    anchor_valid = rng.sample(v4_valid, N_ANCHOR_VALID)

    train = iave_train + anchor_train
    valid = iave_valid + anchor_valid
    rng.shuffle(train)
    rng.shuffle(valid)

    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in [("train", train), ("valid", valid)]:
        with open(OUT / f"{name}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps({"messages": r["messages"]}, ensure_ascii=False) + "\n")

    print(f"train: {len(iave_train)} iave + {len(anchor_train)} v4-anchor = {len(train)}")
    print(f"valid: {len(iave_valid)} iave + {len(anchor_valid)} v4-anchor = {len(valid)}")


if __name__ == "__main__":
    main()
