"""Re-apply harness/verifiers.py's CHECKERS to already-generated responses.

Scoring is a pure function of (item, response text), so a checker fix
doesn't require re-running inference — just re-score the stored
results-<label>.jsonl and rewrite it plus summary-<label>.json in place.

Usage: python -m harness.rescore <label> [<label> ...]
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

from harness.verifiers import CHECKERS

HERE = Path(__file__).parent


def rescore(label):
    results_path = HERE / f"results-{label}.jsonl"
    summary_path = HERE / f"summary-{label}.json"
    items = [json.loads(l) for l in open(results_path)]

    changed = []
    tally = defaultdict(lambda: [0, 0])
    for item in items:
        old_passed = item["passed"]
        passed, reason = CHECKERS[item["category"]](item, item["response"])
        if passed != old_passed:
            changed.append((item["id"], old_passed, passed, reason))
        item["passed"], item["reason"] = passed, reason
        tally[item["category"]][0] += passed
        tally[item["category"]][1] += 1

    with open(results_path, "w") as f:
        for r in items:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    old_summary = json.load(open(summary_path))
    summary = {
        "label": old_summary["label"], "model": old_summary["model"],
        "categories": {c: {"passed": p, "total": t, "rate": round(p / t, 3)}
                       for c, (p, t) in sorted(tally.items())},
    }
    summary["overall"] = round(sum(p for p, _ in tally.values()) / len(items), 3)
    with open(summary_path, "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"{label}: {len(changed)} item(s) changed verdict")
    for id_, old, new, reason in changed:
        print(f"  {id_}: {old} -> {new} ({reason})")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    for label in sys.argv[1:]:
        rescore(label)
