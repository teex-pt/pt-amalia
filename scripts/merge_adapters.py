"""Merge two mlx_lm LoRA adapters by weighted averaging ("adapter soup").

Both adapters must share the same architecture (same layers/rank — true for
any two adapters trained with the same mlx_lm.lora settings on the same base).

Usage:
  python scripts/merge_adapters.py A_DIR B_DIR OUT_DIR --alpha 0.5
    (alpha = weight of A; 1-alpha = weight of B)
"""

import argparse
import shutil
from pathlib import Path

import mlx.core as mx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("out")
    ap.add_argument("--alpha", type=float, default=0.5, help="weight of adapter A")
    args = ap.parse_args()

    wa = mx.load(str(Path(args.a) / "adapters.safetensors"))
    wb = mx.load(str(Path(args.b) / "adapters.safetensors"))
    assert set(wa) == set(wb), (
        f"adapter key mismatch: {len(set(wa) ^ set(wb))} differing keys — "
        "were these trained with the same LoRA settings?")

    merged = {k: args.alpha * wa[k] + (1 - args.alpha) * wb[k] for k in wa}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    mx.save_safetensors(str(out / "adapters.safetensors"), merged)
    shutil.copy(Path(args.a) / "adapter_config.json", out / "adapter_config.json")
    print(f"merged {len(merged)} tensors: {args.alpha:.2f}*{args.a} + "
          f"{1 - args.alpha:.2f}*{args.b} -> {out}")


if __name__ == "__main__":
    main()
