"""Shardable dataset-generation worker — runs on any machine in the fleet.

Generation is embarrassingly parallel: each worker takes a shard of seeded
templates, drafts with its local model, verifies with the code verifiers, and
writes a self-contained JSONL shard. Shards are merged centrally by
merge_shards.py. No coordination or network needed during generation.

Backends:
  --backend mlx   local MLX model (Apple Silicon)
  --backend api   any OpenAI-compatible endpoint (llama-server on the CUDA box:
                  `llama-server -m AMALIA-9B-0626-DPO-Q4_K_M.gguf --port 8080`)

Roles (which stage this worker performs):
  --role draft     stage-1 teacher for arithmetic+format (verify-early: passing
                   drafts are final; failing ones are queued for rewrite)
  --role onpolicy  variety+honesty answered directly by the model (use AMALIA
                   for honesty — DPO negatives must come from the student)

Examples:
  # M5 Pro (this machine), Ministral drafting shard 0 of 4:
  python -m datagen.worker --role draft --backend mlx \
      --model mlx-community/Ministral-3-14B-Reasoning-2512-4bit \
      --shard 0 --num-shards 4 --per-category 50

  # M1 16GB, same but shard 1:
  python -m datagen.worker --role draft --backend mlx --model <same> --shard 1 ...

  # Ryzen + RTX 4060 Ti serving AMALIA GGUF via llama-server, on-policy shard 2:
  python -m datagen.worker --role onpolicy --backend api \
      --api-base http://localhost:8080/v1 --model amalia \
      --shard 2 --num-shards 4 --per-category 50
"""

import argparse
import json
import platform
import re
import time
import urllib.request
from pathlib import Path

from datagen.templates import make_shard
from harness.verifiers import CHECKERS, VERIFIER_VERSION, find_br_markers

THINK_RE = re.compile(r"\[THINK\].*?\[/THINK\]|<think>.*?</think>", re.DOTALL)
MAX_TOKENS = {"arithmetic": 2048, "format": 2048, "variety": 200, "honesty": 200}


class MLXBackend:
    def __init__(self, model_path):
        import mlx.core as mx
        from mlx_lm import load, stream_generate
        try:
            mx.set_memory_limit(12 * 1024**3)
        except Exception:
            pass
        self._mx = mx
        self._stream = stream_generate
        self.model, self.tokenizer = load(
            model_path, tokenizer_config={"fix_mistral_regex": True})

    def generate(self, prompt, max_tokens):
        ids = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], add_generation_prompt=True)
        text = ""
        for r in self._stream(self.model, self.tokenizer, ids, max_tokens=max_tokens):
            text += r.text
        self._mx.clear_cache()
        return text.strip()


class APIBackend:
    def __init__(self, api_base, model):
        self.url = api_base.rstrip("/") + "/chat/completions"
        self.model = model

    def generate(self, prompt, max_tokens):
        body = json.dumps({
            "model": self.model, "temperature": 0, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            self.url, body, {"Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=600) as resp:
                    data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"].strip()
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", choices=["draft", "onpolicy"], required=True)
    ap.add_argument("--backend", choices=["mlx", "api"], required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-base", default="http://localhost:8080/v1")
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--num-shards", type=int, required=True)
    ap.add_argument("--per-category", type=int, default=50)
    ap.add_argument("--categories", nargs="+", default=None,
                    help="restrict to these categories (subset of the role's)")
    args = ap.parse_args()

    wanted = ("arithmetic", "format") if args.role == "draft" else ("variety", "honesty")
    if args.categories:
        wanted = tuple(c for c in wanted if c in args.categories)
    items = [i for i in make_shard(args.shard, args.per_category)
             if i["category"] in wanted]

    backend = (MLXBackend(args.model) if args.backend == "mlx"
               else APIBackend(args.api_base, args.model))

    out_dir = Path(__file__).parent / "out"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"shard-{args.shard:03d}-{args.role}-{platform.node().split('.')[0]}.jsonl"

    t0, n_pass = time.time(), 0
    with open(out_path, "w") as f:
        for n, it in enumerate(items, 1):
            raw = backend.generate(it["prompt"], MAX_TOKENS[it["category"]])
            trace = THINK_RE.findall(raw)
            final = THINK_RE.sub("", raw).strip()
            ok, reason = CHECKERS[it["category"]](it, final)
            if ok and it["category"] in ("arithmetic", "format") and find_br_markers(final):
                ok, reason = False, f"pt-BR markers: {find_br_markers(final)}"
            disposition = (
                "sft" if ok and it["category"] != "honesty"
                else "dpo_chosen" if ok
                else "dpo_rejected" if it["category"] == "honesty"
                else "rewrite_queue" if args.role == "draft"
                else "dpo_rejected")
            n_pass += ok
            f.write(json.dumps({
                **it, "final": final,
                "verifier": {"passed": ok, "reason": reason, "version": VERIFIER_VERSION},
                "disposition": disposition,
                "provenance": {"model": args.model, "role": args.role,
                               "backend": args.backend, "shard": args.shard,
                               "host": platform.node(),
                               "trace": trace[0] if trace else None},
            }, ensure_ascii=False) + "\n")
            if n % 10 == 0:
                rate = n / (time.time() - t0)
                print(f"{n}/{len(items)} ({n_pass} passed, {rate:.1f} items/s)", flush=True)

    print(f"done: {out_path} — {n_pass}/{len(items)} passed verification")


if __name__ == "__main__":
    main()
