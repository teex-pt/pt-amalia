"""Convert datagen/iave/extracted.jsonl into the project's standard mix
schema (messages: user/assistant), for the K-12 tutor specialization line.

Each MCQ becomes a chat pair: the question+options as the user turn, a short
answer statement citing the correct option as the assistant turn. Ground
truth is the official IAVE marking scheme - never inferred by a model.
Two-version exams (shuffled options) each produce their own record, since
the correct letter differs between versions.

A whole-sitting slice is reserved for harness/iave_prompts.jsonl (held-out
evaluation) BEFORE the train/valid split, not carved from mix/valid.jsonl
after the fact: items within one exam sitting can share a reading passage
or stimulus, so excluding at the row/item level still leaks generalization
signal between train and eval. Reservation happens at (code, phase)
granularity instead.

Usage: python -m datagen.iave_build_mix
Writes datagen/iave/mix/{train,valid}.jsonl and harness/iave_prompts.jsonl
"""

import json
import random
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).parent / "iave" / "extracted.jsonl"
OUT = Path(__file__).parent / "iave" / "mix"
HARNESS_OUT = Path(__file__).parent.parent / "harness" / "iave_prompts.jsonl"

# ~ control_prompts_v3.jsonl scale (36 rows) - big enough for a per-subject
# read, small enough to leave the training pool mostly intact.
RESERVED_TARGET_ROWS = 36


def build_prompt(r):
    return (f"[Exame Nacional de {r['subject']}, {r['year']}, item {r['item']}]\n\n"
            f"{r['question']}\n\nQual é a opção correta? Responde apenas com a letra.")


def to_messages(r, version, answer):
    return {
        "messages": [{"role": "user", "content": build_prompt(r)},
                     {"role": "assistant", "content": f"({answer})"}],
        "subject": r["subject"], "year": r["year"], "phase": r["phase"],
        "item": r["item"], "version": version, "notation_risk": r["notation_risk"],
    }


def to_harness_prompt(r, version, answer):
    item_id = r["item"].rstrip(".")
    return {
        "id": f"iave-{r['code']}-{r['phase']}-{item_id}-v{version}",
        "category": "mcq", "subtype": "iave_mcq",
        "prompt": build_prompt(r), "answer": answer,
        "subject": r["subject"], "year": r["year"], "phase": r["phase"],
        "code": r["code"], "item": r["item"], "version": version,
        "notation_risk": r["notation_risk"],
    }


def reserve_sittings(sittings):
    """Reserve whole sittings for held-out harness eval: smallest first, at
    most one sitting per subject code, until the target row count is
    reached. Smallest-first avoids one large sitting (e.g. Economia A's
    56-row F2) dominating the eval set and gutting that subject's training
    data; the one-per-code cap maximizes subject diversity for the same
    row budget. Deterministic - no seed needed."""
    def n_rows(sid):
        return sum(1 + (1 if r["answer_v2"] else 0) for r in sittings[sid])

    ids = sorted(sittings.keys(), key=lambda sid: (n_rows(sid), sid))
    reserved, reserved_rows, seen_codes = [], 0, set()
    for sid in ids:
        if reserved_rows >= RESERVED_TARGET_ROWS:
            break
        code = sid[0]
        if code in seen_codes:
            continue
        reserved.append(sid)
        reserved_rows += n_rows(sid)
        seen_codes.add(code)
    remaining = [sid for sid in sittings if sid not in reserved]
    return reserved, remaining


def main():
    records = [json.loads(line) for line in open(SRC)]
    sittings = defaultdict(list)
    for r in records:
        sittings[(r["code"], r["phase"])].append(r)

    reserved_ids, remaining_ids = reserve_sittings(sittings)

    harness_rows = []
    for sid in reserved_ids:
        for r in sittings[sid]:
            harness_rows.append(to_harness_prompt(r, 1, r["answer_v1"]))
            if r["answer_v2"]:
                harness_rows.append(to_harness_prompt(r, 2, r["answer_v2"]))

    HARNESS_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(HARNESS_OUT, "w") as f:
        for row in harness_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    rows = []
    for sid in remaining_ids:
        for r in sittings[sid]:
            rows.append(to_messages(r, 1, r["answer_v1"]))
            if r["answer_v2"]:
                rows.append(to_messages(r, 2, r["answer_v2"]))

    rng = random.Random(9001)  # disjoint from harness (42) and other mixes
    rng.shuffle(rows)
    n_valid = max(20, len(rows) // 10)

    OUT.mkdir(parents=True, exist_ok=True)
    for name, chunk in [("valid", rows[:n_valid]), ("train", rows[n_valid:])]:
        with open(OUT / f"{name}.jsonl", "w") as f:
            for r in chunk:
                f.write(json.dumps({"messages": r["messages"]}, ensure_ascii=False) + "\n")

    n_risk = sum(1 for r in rows if r["notation_risk"])
    subjects = sorted({r["subject"] for sid in reserved_ids for r in sittings[sid]})
    print(f"harness eval: {len(reserved_ids)} sittings reserved, {len(harness_rows)} mcq prompts "
          f"-> harness/iave_prompts.jsonl, subjects: {', '.join(subjects)}")
    print(f"training pool: {len(rows)} total ({len(rows) - n_valid} train, {n_valid} valid); "
          f"{n_risk} flagged notation_risk ({n_risk/len(rows):.0%})")


if __name__ == "__main__":
    main()
