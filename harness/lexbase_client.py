"""Minimal MCP client for the lexbase.pt legislation service (leis-pt's
production RAG retrieval layer, no generation tool by design - see
JOURNAL.md 2026-07-14). Provides a plain async function to call
search_legislation and get back anchored results (citation + article text
+ in-force dates), for bridging into a local generator model.

Usage as a library:
    from harness.lexbase_client import search_legislation
    results = await search_legislation("despedimento por justa causa", k=6)

Usage as a CLI sanity check:
    python -m harness.lexbase_client --list-tools
    python -m harness.lexbase_client --query "despedimento por justa causa"
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv(Path(__file__).parent.parent / ".env")

LEXBASE_URL = "https://api.lexbase.pt/mcp-key/"


def _headers():
    key = os.environ.get("LEXBASE_API_KEY")
    if not key:
        raise RuntimeError("LEXBASE_API_KEY not set (expected in .env)")
    return {"Authorization": f"Bearer {key}"}


async def list_tools():
    async with streamablehttp_client(LEXBASE_URL, headers=_headers()) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools()
            return [{"name": t.name, "description": t.description,
                     "inputSchema": t.inputSchema} for t in resp.tools]


async def call_tool(name, arguments):
    async with streamablehttp_client(LEXBASE_URL, headers=_headers()) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.call_tool(name, arguments)
            texts = [c.text for c in resp.content if c.type == "text"]
            return "\n".join(texts)


async def search_legislation(query, k=8, tipo=None, tema_tag_id=None, in_force_only=True):
    args = {"query": query, "k": k, "in_force_only": in_force_only}
    if tipo:
        args["tipo"] = tipo
    if tema_tag_id:
        args["tema_tag_id"] = tema_tag_id
    raw = await call_tool("search_legislation", args)
    return json.loads(raw)


MAX_EXCERPT_CHARS = 1500


def build_prompt(query, hits, include_breadcrumb=False):
    """Two variants, both real:
    - include_breadcrumb=False (default): matches the legal-v2 SFT
      training data's citation format exactly (designacao + nome +
      epigrafe, no breadcrumb).
    - include_breadcrumb=True: matches lexbase.pt's production RAG
      integration's prompt shape, which appends " — {breadcrumb}" after
      the citation on the [F#] line. Test both rather than assume one
      predicts the other.
    """
    lines = [f"PERGUNTA: {query}", "", "EXCERTOS:"]
    for i, h in enumerate(hits, 1):
        vig = h["in_force"].get("data_entrada_vigor")
        tag_line = f"[F{i}] {h['citation']}"
        if include_breadcrumb and h.get("breadcrumb"):
            tag_line += f" — {' › '.join(h['breadcrumb'])}"
        lines.append(tag_line)
        lines.append(f"«{h['texto'][:MAX_EXCERPT_CHARS]}»")
        if vig:
            lines.append(f"(em vigor desde {vig[:10]})")
        lines.append("")
    return "\n".join(lines).strip(), len(hits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-tools", action="store_true")
    ap.add_argument("--query")
    ap.add_argument("--k", type=int, default=6)
    args = ap.parse_args()

    if args.list_tools:
        tools = asyncio.run(list_tools())
        print(json.dumps(tools, ensure_ascii=False, indent=2))
    elif args.query:
        results = asyncio.run(search_legislation(args.query, k=args.k))
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
