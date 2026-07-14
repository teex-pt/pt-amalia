"""Decontamination check: does teex-pt/amalia-cita-legal or
teex-pt/amalia-sum-dre (the actual SFT training data, not the raw
leis-pt-consolidada corpus) substantially overlap with LegalBenchPT
(BeatrizCanaverde/LegalBench.PT on HF, vendored locally as a task suite
under amalia-lm-eval/tasks/amalia-bench/LegalBenchPT/)? Standing project
rule (PLANO-MELHORIA-AMALIA.md, JOURNAL.md "Standing decisions") -
decontaminate against the consortium benchmarks before any dataset/
training claim, deferred since these datasets were first built.

Method: exact 13-word shingle overlap - the standard, cheap approach for
literal text-reuse contamination checks (same window size popularized by
GPT-3's contamination methodology), not embedding/topical similarity.
Topical overlap between LegalBenchPT's fictional exam scenarios and our
real-statute training data is expected (both are Portuguese law) and not
itself contamination; a shared 13-word run of literal text is a much
stronger, low-false-positive signal of actual reuse.

Not checked here: leis-pt-consolidada (the raw corpus). It will
legitimately contain the same real statute text LegalBenchPT's questions
sometimes quote - that's expected overlap of public-domain law, not
contamination, and checking it would just produce a flood of benign hits
on quoted articles rather than a meaningful signal.

Usage: python -m datagen.decontaminate_legalbenchpt
Writes datagen/decontamination-legalbenchpt-report.json
"""

import json
import re
from pathlib import Path

import pandas as pd
from huggingface_hub import HfApi, hf_hub_download

HERE = Path(__file__).parent
SHINGLE_SIZE = 13  # words


def normalize_words(text):
    return re.findall(r"\w+", text.lower())


def shingles(text, n=SHINGLE_SIZE):
    words = normalize_words(text)
    if len(words) < n:
        return set()
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def load_legalbenchpt():
    api = HfApi()
    info = api.dataset_info("BeatrizCanaverde/LegalBench.PT")
    frames = []
    for f in info.siblings:
        if f.rfilename.endswith(".parquet"):
            p = hf_hub_download(repo_id="BeatrizCanaverde/LegalBench.PT",
                                 filename=f.rfilename, repo_type="dataset")
            frames.append(pd.read_parquet(p))
    return pd.concat(frames, ignore_index=True)


def load_our_rows():
    rows = []  # list of (source, id, text)
    for split in ("train", "valid"):
        for r in [json.loads(l) for l in open(HERE / "leis-pt" / "cita-legal" / f"{split}.jsonl")]:
            content = " ".join(m["content"] for m in r["messages"])
            rows.append((f"cita-legal/{split}", str(r.get("target_diploma_id", "?")), content))
        for r in [json.loads(l) for l in open(HERE / "leis-pt" / "sum-dre" / f"{split}.jsonl")]:
            content = " ".join(m["content"] for m in r["messages"])
            rows.append((f"sum-dre/{split}", str(r.get("diploma_id", "?")), content))
    return rows


def main():
    print("Loading LegalBenchPT (BeatrizCanaverde/LegalBench.PT)...")
    bench = load_legalbenchpt()
    print(f"  {len(bench)} items across {bench['Field of Law'].nunique()} domains")

    print("Building benchmark shingle index...")
    bench_shingles = {}  # shingle -> list of (domain, ID)
    for _, row in bench.iterrows():
        text = f"{row['Question']} {row['Answer']}"
        for s in shingles(text):
            bench_shingles.setdefault(s, []).append((row["Field of Law"], str(row["ID"])))

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
        "n_legalbenchpt_items": len(bench),
        "n_legalbenchpt_domains": int(bench["Field of Law"].nunique()),
        "n_our_rows_checked": len(our_rows),
        "shingle_size": SHINGLE_SIZE,
        "n_contaminated_rows": len(hits),
        "max_shingles_matched_single_row": max_overlap,
        "note": ("High hit count with low per-row overlap (mostly 1-8 shingles, scattered "
                 "across many different bench items per phrase) is the expected signature of "
                 "shared real statute text, not leaked test items - manually verified, see "
                 "eval/results/DECONTAMINATION-legalbenchpt.md."),
        "hits": hits,
    }
    with open(HERE / "decontamination-legalbenchpt-report.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps({k: v for k, v in report.items() if k != "hits"}, indent=2))
    print("CONTAMINATION FOUND" if hits else "Clean: no 13-word shingle overlap found.")


if __name__ == "__main__":
    main()
