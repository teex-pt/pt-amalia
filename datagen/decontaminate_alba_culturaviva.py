"""Decontamination check: does teex-pt/amalia-cita-legal or
teex-pt/amalia-sum-dre overlap with ALBA (amalia-llm/alba_mcq - Portuguese
linguistics MCQs: morphology, syntax, semantics, discourse, phonetics,
lexicology, language variety, word play) or CulturaVivaPT
(amalia-llm/cultura-viva-pt-mcq - Portuguese culture/trivia MCQs)? The
other two of the four consortium benchmarks named in this project's
standing decontamination rule, alongside LegalBenchPT and pt_exams (see
decontaminate_legalbenchpt.py for the full method rationale). Lower
priority than those two - linguistics puzzles and culture trivia have
even less topical overlap with a legal-citation corpus than pt_exams
already had - but checked rather than assumed clean.

Usage: python -m datagen.decontaminate_alba_culturaviva
Writes datagen/decontamination-alba-report.json and
datagen/decontamination-culturaviva-report.json
"""

import json
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

from datagen.decontaminate_legalbenchpt import shingles, load_our_rows

HERE = Path(__file__).parent


def load_alba():
    api = HfApi()
    info = api.dataset_info("amalia-llm/alba_mcq")
    items = []
    for f in info.siblings:
        if not f.rfilename.endswith(".json"):
            continue
        p = hf_hub_download(repo_id="amalia-llm/alba_mcq", filename=f.rfilename, repo_type="dataset")
        for r in json.load(open(p)):
            text = f"{r['question']} {' '.join(r.get('choices') or [])}"
            items.append({"key": (r.get("subject"), r.get("id")), "text": text})
    return items


def load_culturaviva():
    p = hf_hub_download(repo_id="amalia-llm/cultura-viva-pt-mcq",
                         filename="ptculcov_new_mcq.jsonl", repo_type="dataset")
    items = []
    for line in open(p):
        r = json.loads(line)
        choices_text = " ".join(r.get("choices", {}).get("text") or [])
        text = f"{r['question']} {choices_text}"
        items.append({"key": (r.get("domain"), r.get("id")), "text": text})
    return items


def check(name, bench_items, our_rows):
    print(f"\n=== {name}: {len(bench_items)} items ===")
    bench_shingles = {}
    for item in bench_items:
        for s in shingles(item["text"]):
            bench_shingles.setdefault(s, []).append(item["key"])

    hits = []
    for source, item_id, text in our_rows:
        overlap = shingles(text) & bench_shingles.keys()
        if overlap:
            bench_hits = sorted({str(bh) for s in overlap for bh in bench_shingles[s]})
            hits.append({
                "source": source, "id": item_id, "n_shingles_matched": len(overlap),
                "example_shingle": next(iter(overlap)), "bench_items": bench_hits[:5],
            })

    max_overlap = max((h["n_shingles_matched"] for h in hits), default=0)
    report = {
        "n_bench_items": len(bench_items),
        "n_our_rows_checked": len(our_rows),
        "shingle_size": 13,
        "n_contaminated_rows": len(hits),
        "max_shingles_matched_single_row": max_overlap,
        "hits": hits,
    }
    with open(HERE / f"decontamination-{name}-report.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != "hits"}, indent=2))
    print("CONTAMINATION FOUND" if hits else "Clean: no 13-word shingle overlap found.")
    return report


def main():
    print("Loading our training rows (amalia-cita-legal + amalia-sum-dre)...")
    our_rows = load_our_rows()
    print(f"  {len(our_rows)} rows")

    print("Loading ALBA (amalia-llm/alba_mcq)...")
    alba_items = load_alba()
    check("alba", alba_items, our_rows)

    print("Loading CulturaVivaPT (amalia-llm/cultura-viva-pt-mcq)...")
    cv_items = load_culturaviva()
    check("culturaviva", cv_items, our_rows)


if __name__ == "__main__":
    main()
