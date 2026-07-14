"""Same end-to-end RAG integration test as rag_integration_test.py (real
retrieval via lexbase.pt's search_legislation, piped into a generator),
but for an Anthropic API model instead of a local MLX checkpoint. Shares
the exact same build_prompt (harness/lexbase_client.py) so results are
directly comparable to the local-model runs.

Usage:
    python -m harness.rag_integration_test_anthropic --model claude-sonnet-5 \
        --label rag-sonnet5 --queries harness/rag_test_queries.jsonl \
        [--include-breadcrumb]
"""

import argparse
import asyncio
import json
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from harness.lexbase_client import search_legislation, build_prompt

load_dotenv(Path(__file__).parent.parent / ".env")

HERE = Path(__file__).parent
MAX_GEN_TOKENS = 400
FTAG_RE = re.compile(r"\[F(\d+)\]")


def generate(client, model, prompt, max_tokens=MAX_GEN_TOKENS):
    resp = client.messages.create(
        model=model, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Anthropic model id, e.g. claude-sonnet-5")
    ap.add_argument("--label", required=True)
    ap.add_argument("--queries", default="harness/rag_test_queries.jsonl")
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--include-breadcrumb", action="store_true")
    args = ap.parse_args()

    queries = [json.loads(l)["query"] for l in open(args.queries)]
    client = anthropic.Anthropic()

    results = []
    for n, query in enumerate(queries, 1):
        print(f"[{n}/{len(queries)}] {query}")
        hits = asyncio.run(search_legislation(query, k=args.k))["hits"]
        if not hits:
            results.append({"query": query, "n_hits": 0, "prompt": None,
                             "response": None, "note": "empty retrieval"})
            print("  no hits")
            continue
        prompt, n_hits = build_prompt(query, hits, include_breadcrumb=args.include_breadcrumb)
        response = generate(client, args.model, prompt)
        tags_used = sorted({int(t) for t in FTAG_RE.findall(response)})
        results.append({
            "query": query, "n_hits": n_hits, "prompt": prompt, "response": response,
            "tags_used": tags_used,
            "hit_citations": [h["citation"] for h in hits],
        })
        print(f"  {n_hits} hits, tags used: {tags_used}")

    out_path = HERE / f"rag-results-{args.label}.jsonl"
    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
