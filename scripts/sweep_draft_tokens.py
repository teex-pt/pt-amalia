"""Sweep --num-draft-tokens to find the speedup/overhead tradeoff per prompt type.

mlx_lm's own default is num_draft_tokens=2 (not the 4-8 often assumed).
The distilled EuroLLM-1.7B benchmark showed a 0.43x slowdown on short bare
answers at that default; this sweep tests whether tuning the value changes
that, or whether it's a structural draft/verify overhead problem regardless
of N (see PILOT/JOURNAL discussion).

Usage: python scripts/sweep_draft_tokens.py --draft-model <path>
Writes scripts/sweep-results.json.
"""

import argparse
import json
import re
import subprocess

TPS_RE = re.compile(r"Generation: \d+ tokens, ([\d.]+) tokens-per-sec")

PROMPTS = [
    ("General Physics", "Explica-me o que é a gravidade, focando no espaço-tempo e na relatividade geral."),
    ("Honesty (Fake Entity)", "Quem foi o poeta António Silva de Lemos que escreveu a obra O Canto da Saudade em 2031?"),
    ("Arithmetic (Bare)", "Responde apenas com o resultado. Quanto é 142 + 258?"),
]

N_VALUES = [1, 2, 3, 4, 6, 8, 12]


def get_tps(output):
    m = TPS_RE.search(output)
    return float(m.group(1)) if m else 0.0


def run_generate(target_model, prompt, max_tokens, draft_model=None, num_draft_tokens=None):
    cmd = [".venv/bin/mlx_lm.generate", "--model", target_model,
           "--prompt", prompt, "--max-tokens", str(max_tokens)]
    if draft_model:
        cmd += ["--draft-model", draft_model]
    if num_draft_tokens is not None:
        cmd += ["--num-draft-tokens", str(num_draft_tokens)]
    out = subprocess.run(cmd, capture_output=True, text=True)
    return get_tps(out.stdout + out.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-model", default="amalia-mlx-8bit")
    ap.add_argument("--draft-model", required=True)
    ap.add_argument("--max-tokens", type=int, default=100)
    args = ap.parse_args()

    baseline = {}
    for name, prompt in PROMPTS:
        tps = run_generate(args.target_model, prompt, args.max_tokens)
        baseline[name] = tps
        print(f"baseline {name}: {tps:.2f} tok/s", flush=True)

    results = []
    for n in N_VALUES:
        for name, prompt in PROMPTS:
            tps = run_generate(args.target_model, prompt, args.max_tokens,
                               draft_model=args.draft_model, num_draft_tokens=n)
            speedup = tps / baseline[name] if baseline[name] > 0 else 0.0
            print(f"N={n:2d}  {name:24s} {tps:6.2f} tok/s  ({speedup:.2f}x)", flush=True)
            results.append({"n": n, "prompt": name, "tps": tps,
                            "baseline_tps": baseline[name], "speedup": speedup})

    with open("scripts/sweep-results.json", "w") as f:
        json.dump({"baseline": baseline, "sweep": results}, f, ensure_ascii=False, indent=2)

    print("\n=== Best N per prompt type ===")
    for name, _ in PROMPTS:
        rows = [r for r in results if r["prompt"] == name]
        best = max(rows, key=lambda r: r["speedup"])
        print(f"{name}: best N={best['n']} -> {best['speedup']:.2f}x")

    print("\n=== Average speedup per N ===")
    for n in N_VALUES:
        rows = [r for r in results if r["n"] == n]
        avg = sum(r["speedup"] for r in rows) / len(rows)
        print(f"N={n:2d}: avg {avg:.2f}x")


if __name__ == "__main__":
    main()
