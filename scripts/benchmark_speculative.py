"""Benchmark speculative decoding speedup: AMALIA-9B target, EuroLLM-1.7B draft.

Compares generation tokens/sec with and without --draft-model across three
representative prompt types (general knowledge, honesty/fake-entity,
arithmetic). The draft model should be a distilled EuroLLM-1.7B aligned to
AMALIA's exact greedy phrasing (see datagen/distill_mix.py) — closer
alignment means more draft tokens get accepted by the target, and a higher
speedup.

Usage: python scripts/benchmark_speculative.py --draft-model <path>
"""

import argparse
import re
import subprocess

TPS_RE = re.compile(r"Generation: \d+ tokens, ([\d.]+) tokens-per-sec")

PROMPTS = [
    ("General Physics", "Explica-me o que é a gravidade, focando no espaço-tempo e na relatividade geral."),
    ("Honesty (Fake Entity)", "Quem foi o poeta António Silva de Lemos que escreveu a obra O Canto da Saudade em 2031?"),
    ("Arithmetic (Bare)", "Responde apenas com o resultado. Quanto é 142 + 258?"),
]


def get_tps(output):
    m = TPS_RE.search(output)
    return float(m.group(1)) if m else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-model", default="amalia-mlx-8bit")
    ap.add_argument("--draft-model", required=True)
    ap.add_argument("--max-tokens", type=int, default=100)
    args = ap.parse_args()

    results = []
    for name, prompt in PROMPTS:
        print(f"\n=== Benchmark: {name} ===", flush=True)

        cmd_no_draft = [".venv/bin/mlx_lm.generate", "--model", args.target_model,
                        "--prompt", prompt, "--max-tokens", str(args.max_tokens)]
        out_no_draft = subprocess.run(cmd_no_draft, capture_output=True, text=True)
        tps_no_draft = get_tps(out_no_draft.stdout + out_no_draft.stderr)

        cmd_draft = [".venv/bin/mlx_lm.generate", "--model", args.target_model,
                    "--draft-model", args.draft_model,
                    "--prompt", prompt, "--max-tokens", str(args.max_tokens)]
        out_draft = subprocess.run(cmd_draft, capture_output=True, text=True)
        tps_draft = get_tps(out_draft.stdout + out_draft.stderr)

        speedup = tps_draft / tps_no_draft if tps_no_draft > 0 else 0.0
        print(f"Tokens/Sec (No Draft):   {tps_no_draft:.2f}")
        print(f"Tokens/Sec (With Draft): {tps_draft:.2f}")
        print(f"Speedup: {speedup:.2f}x")
        results.append({"name": name, "tps_no_draft": tps_no_draft,
                        "tps_draft": tps_draft, "speedup": speedup})

    print("\n=== Summary ===")
    for r in results:
        print(f"{r['name']}: {r['tps_no_draft']:.1f} -> {r['tps_draft']:.1f} tok/s ({r['speedup']:.2f}x)")
    avg_speedup = sum(r["speedup"] for r in results) / len(results)
    print(f"Average speedup: {avg_speedup:.2f}x")


if __name__ == "__main__":
    main()
