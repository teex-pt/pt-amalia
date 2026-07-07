"""Download IAVE exam PDFs from datagen/iave_registry.py.

Respectful crawl: sequential, rate-limited, identified User-Agent, resumable
(skips files already on disk). Writes to datagen/iave/raw/{year}/{code}_{phase}_{kind}.pdf

Usage: python -m datagen.iave_download [--delay 2.0]
"""

import argparse
import time
import urllib.request
from pathlib import Path

from datagen.iave_registry import EXAMS

HEADERS = {"User-Agent": "pt-amalia research crawler (github.com/teex-pt/pt-amalia) - "
                         "educational NLP dataset build, respectful low-rate crawl"}


def fetch(url, dest, delay):
    if dest.exists() and dest.stat().st_size > 0:
        return "cached"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        dest.write_bytes(data)
        time.sleep(delay)
        return "ok"
    except Exception as e:
        return f"FAILED: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between requests")
    args = ap.parse_args()

    out_root = Path(__file__).parent / "iave" / "raw"
    results = {"ok": 0, "cached": 0, "failed": 0}

    for year, subject, code, phase, exam_url, cc_url in EXAMS:
        year_dir = out_root / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        for kind, url in (("exam", exam_url), ("cc", cc_url)):
            dest = year_dir / f"{code}_{phase}_{kind}.pdf"
            status = fetch(url, dest, args.delay)
            key = "failed" if status.startswith("FAILED") else status
            results[key] += 1
            print(f"[{status}] {year} {subject} ({code}) {phase} {kind}", flush=True)

    print(f"\ndone: {results['ok']} downloaded, {results['cached']} cached, {results['failed']} failed")


if __name__ == "__main__":
    main()
