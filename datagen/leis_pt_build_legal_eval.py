"""Reserve a diploma-disjoint held-out slice of amalia-cita-legal for the
harness's deterministic legal_cita/legal_refusal categories - the same
"reserve before treating the rest as trainable" discipline
iave_build_mix.py uses for MCQ sittings (see reserve_sittings there),
applied here at the row level: cita-legal/valid.jsonl is already
diploma-disjoint from train.jsonl by construction (see the
amalia-cita-legal dataset card for how that split was built), so
reserving rows out of valid.jsonl keeps train.jsonl untouched and still
guarantees no diploma crosses from training into this benchmark.

Usage: python -m datagen.leis_pt_build_legal_eval
Writes harness/legal_cita_prompts.jsonl and rewrites
datagen/leis-pt/cita-legal/valid.jsonl to exclude the reserved rows.
"""

import json
import random
from pathlib import Path

VALID_PATH = Path(__file__).parent / "leis-pt" / "cita-legal" / "valid.jsonl"
HARNESS_OUT = Path(__file__).parent.parent / "harness" / "legal_cita_prompts.jsonl"

N_GROUNDED = 50
N_REFUSAL = 10
SEED = 73001  # disjoint from harness(42), smoke(7), iave mix(9001), iave-v2-mix(51015)


def load(path):
    return [json.loads(l) for l in open(path)]


def to_harness_prompt(r, idx):
    return {
        "id": f"legal-cita-{r['label']}-{idx}",
        "category": "legal_cita" if r["label"] == "grounded" else "legal_refusal",
        "prompt": r["messages"][0]["content"],
        "n_fragments_used": r["n_fragments_used"],
        "target_diploma_id": r["target_diploma_id"],
    }


def main():
    rows = load(VALID_PATH)
    grounded = [r for r in rows if r["label"] == "grounded"]
    refusal = [r for r in rows if r["label"] == "refusal"]

    rng = random.Random(SEED)
    reserved_grounded = rng.sample(grounded, min(N_GROUNDED, len(grounded)))
    reserved_refusal = rng.sample(refusal, min(N_REFUSAL, len(refusal)))
    reserved_ids = {id(r) for r in reserved_grounded + reserved_refusal}

    harness_rows = [to_harness_prompt(r, i)
                     for i, r in enumerate(reserved_grounded + reserved_refusal)]
    HARNESS_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(HARNESS_OUT, "w") as f:
        for row in harness_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    remaining = [r for r in rows if id(r) not in reserved_ids]
    with open(VALID_PATH, "w") as f:
        for r in remaining:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"reserved {len(reserved_grounded)} grounded + {len(reserved_refusal)} refusal "
          f"-> harness/legal_cita_prompts.jsonl")
    print(f"cita-legal/valid.jsonl: {len(rows)} -> {len(remaining)} rows")


if __name__ == "__main__":
    main()
