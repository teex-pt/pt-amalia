"""Merge worker shards into dataset splits, with central re-verification.

Reads datagen/out/*.jsonl from all machines, deduplicates by item id (first
occurrence wins), re-runs the verifiers on every final text (workers may have
run an older verifier version), and writes:

  datagen/merged/sft.jsonl            verified SFT samples (chat format)
  datagen/merged/dpo.jsonl            honesty chosen/rejected candidates
  datagen/merged/rewrite_queue.jsonl  correct-but-unclean drafts for stage 2
  datagen/merged/stats.json           per-category/per-host yield report

Usage: python -m datagen.merge_shards
"""

import json
from collections import defaultdict
from pathlib import Path

from harness.verifiers import CHECKERS, VERIFIER_VERSION


def main():
    out_dir = Path(__file__).parent / "out"
    merged_dir = Path(__file__).parent / "merged"
    merged_dir.mkdir(exist_ok=True)

    seen, records = set(), []
    for shard_file in sorted(out_dir.glob("*.jsonl")):
        for line in open(shard_file):
            r = json.loads(line)
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            ok, reason = CHECKERS[r["category"]](r, r["final"])
            r["verifier"] = {"passed": ok, "reason": reason, "version": VERIFIER_VERSION}
            records.append(r)

    stats = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    sft, dpo, rewrite = [], [], []
    for r in records:
        host = r["provenance"].get("host", "?").split(".")[0]
        s = stats[r["category"]][host]
        s[0] += r["verifier"]["passed"]
        s[1] += 1
        if r["category"] == "honesty":
            dpo.append(r)
        elif r["verifier"]["passed"]:
            sft.append({
                "messages": [{"role": "user", "content": r["prompt"]},
                             {"role": "assistant", "content": r["final"]}],
                "category": r["category"], "id": r["id"],
                "provenance": r["provenance"], "verifier": r["verifier"]})
        elif r.get("disposition") == "rewrite_queue":
            rewrite.append(r)

    for name, rows in [("sft", sft), ("dpo", dpo), ("rewrite_queue", rewrite)]:
        with open(merged_dir / f"{name}.jsonl", "w") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = {
        "total_records": len(records),
        "sft": len(sft), "dpo_candidates": len(dpo), "rewrite_queue": len(rewrite),
        "verifier_version": VERIFIER_VERSION,
        "yield_by_category_and_host": {
            cat: {host: {"passed": p, "total": t, "rate": round(p / t, 3)}
                  for host, (p, t) in hosts.items()}
            for cat, hosts in stats.items()},
    }
    with open(merged_dir / "stats.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
