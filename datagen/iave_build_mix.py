"""Convert datagen/iave/extracted.jsonl into the project's standard mix
schema (messages: user/assistant), for the K-12 tutor specialization line.

Each MCQ becomes a chat pair: the question+options as the user turn, a short
answer statement citing the correct option as the assistant turn. Ground
truth is the official IAVE marking scheme - never inferred by a model.
Two-version exams (shuffled options) each produce their own record, since
the correct letter differs between versions.

Usage: python -m datagen.iave_build_mix
Writes datagen/iave/mix/{train,valid}.jsonl
"""

import json
import random
from pathlib import Path

SRC = Path(__file__).parent / "iave" / "extracted.jsonl"
OUT = Path(__file__).parent / "iave" / "mix"


def to_messages(r, version, answer):
    prompt = (f"[Exame Nacional de {r['subject']}, {r['year']}, item {r['item']}]\n\n"
             f"{r['question']}\n\nQual é a opção correta? Responde apenas com a letra.")
    return {
        "messages": [{"role": "user", "content": prompt},
                     {"role": "assistant", "content": f"({answer})"}],
        "subject": r["subject"], "year": r["year"], "phase": r["phase"],
        "item": r["item"], "version": version, "notation_risk": r["notation_risk"],
    }


def main():
    rows = []
    for line in open(SRC):
        r = json.loads(line)
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
    print(f"{len(rows)} total ({len(rows) - n_valid} train, {n_valid} valid); "
          f"{n_risk} flagged notation_risk ({n_risk/len(rows):.0%})")


if __name__ == "__main__":
    main()
