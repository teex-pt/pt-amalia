"""End-to-end RAG integration test: real retrieval (lexbase.pt's
search_legislation MCP tool, leis-pt's production index) piped into a
local generator model (AMALIA baseline or an adapter), instead of the
offline harness's fixed excerpt sets in legal_cita_prompts.jsonl. This is
the piece none of this project's legal-domain evals have tested yet -
retrieval quality and citation behavior together, not citation behavior
alone given hand-picked excerpts.

Prompt format defaults to matching legal-v2's SFT training data exactly
(citation format "{designacao}, {nome}{epigrafe}", no breadcrumb) - pass
--include-breadcrumb to instead match lexbase.pt's actual production
prompt shape, which appends the breadcrumb after the citation. Test both
rather than assume one predicts the other.

Usage:
    python -m harness.rag_integration_test --model amalia-llm/AMALIA-9B-0626-DPO \
        --label rag-baseline --queries harness/rag_test_queries.jsonl

    python -m harness.rag_integration_test --model amalia-llm/AMALIA-9B-0626-DPO \
        --adapter-path adapters/legal-v2 --label rag-legal-v2-prod \
        --queries harness/rag_test_queries.jsonl --include-breadcrumb

Writes harness/rag-results-<label>.jsonl (query, retrieved hits, prompt,
response) for manual review - no automated pass/fail scoring, since real
retrieval means there's no single "correct" excerpt set to check tag
validity against the way the offline harness does.
"""

import argparse
import asyncio
import json
import re
from pathlib import Path

import mlx.core as mx

try:
    mx.set_memory_limit(24 * 1024**3)
    mx.set_wired_limit(20 * 1024**3)
except Exception:
    pass

from mlx_lm import load, stream_generate

from harness.lexbase_client import search_legislation, build_prompt

HERE = Path(__file__).parent
MAX_GEN_TOKENS = 400
FTAG_RE = re.compile(r"\[F(\d+)\]")


def generate(model, tokenizer, prompt, max_tokens=MAX_GEN_TOKENS):
    ids = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], add_generation_prompt=True)
    text = ""
    for r in stream_generate(model, tokenizer, ids, max_tokens=max_tokens):
        text += r.text
    mx.clear_cache()
    return text.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter-path", default=None)
    ap.add_argument("--label", required=True)
    ap.add_argument("--queries", default="harness/rag_test_queries.jsonl")
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--include-breadcrumb", action="store_true",
                    help="match lexbase.pt's actual production prompt shape")
    args = ap.parse_args()

    queries = [json.loads(l)["query"] for l in open(args.queries)]

    print(f"Loading model {args.model} (adapter={args.adapter_path})...")
    model, tokenizer = load(args.model, adapter_path=args.adapter_path)

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
        response = generate(model, tokenizer, prompt)
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
