"""Decontamination check: does teex-pt/amalia-cita-legal or
teex-pt/amalia-sum-dre overlap with pt_exams (amalia-llm/pt_exams, aka
PHEB - Portuguese high-school exam MCQs, 2006-2023, vendored locally
under amalia-lm-eval/tasks/amalia-bench/pt_exams/)? Same standing rule and
method as decontaminate_legalbenchpt.py (13-word shingle overlap) - see
that script for the full rationale. Domain mismatch (K-12 subjects:
Portuguese, Maths, History, Geography, Biology/Geology, Philosophy, vs.
our legal-text corpus) makes near-zero overlap the expectation, not the
assumption - still checked rather than skipped.

Usage: python -m datagen.decontaminate_pt_exams
Writes datagen/decontamination-pt_exams-report.json
"""

import json
from pathlib import Path

from huggingface_hub import hf_hub_download

from datagen.decontaminate_legalbenchpt import shingles, load_our_rows

HERE = Path(__file__).parent


def load_pt_exams():
    p = hf_hub_download(repo_id="amalia-llm/pt_exams", filename="all.json", repo_type="dataset")
    return json.load(open(p))


def main():
    print("Loading pt_exams (amalia-llm/pt_exams)...")
    exams = load_pt_exams()
    subjects = sorted({e["subject"] for e in exams})
    print(f"  {len(exams)} items across {len(subjects)} subjects: {', '.join(subjects)}")

    print("Building benchmark shingle index...")
    bench_shingles = {}  # shingle -> list of (subject, year, question_number)
    for e in exams:
        text = f"{e['question']} {' '.join(e.get('choices') or [])}"
        key = (e["subject"], e["year"], str(e["question_number"]))
        for s in shingles(text):
            bench_shingles.setdefault(s, []).append(key)

    print("Loading amalia-cita-legal + amalia-sum-dre training rows...")
    our_rows = load_our_rows()
    print(f"  {len(our_rows)} rows")

    hits = []
    for source, item_id, text in our_rows:
        overlap = shingles(text) & bench_shingles.keys()
        if overlap:
            bench_hits = sorted({bh for s in overlap for bh in bench_shingles[s]})
            hits.append({
                "source": source, "id": item_id, "n_shingles_matched": len(overlap),
                "example_shingle": next(iter(overlap)), "bench_items": bench_hits[:5],
            })

    max_overlap = max((h["n_shingles_matched"] for h in hits), default=0)
    report = {
        "n_pt_exams_items": len(exams),
        "n_pt_exams_subjects": len(subjects),
        "n_our_rows_checked": len(our_rows),
        "shingle_size": 13,
        "n_contaminated_rows": len(hits),
        "max_shingles_matched_single_row": max_overlap,
        "hits": hits,
    }
    with open(HERE / "decontamination-pt_exams-report.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps({k: v for k, v in report.items() if k != "hits"}, indent=2))
    print("CONTAMINATION FOUND" if hits else "Clean: no 13-word shingle overlap found.")


if __name__ == "__main__":
    main()
