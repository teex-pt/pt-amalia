"""Extract MCQ question+answer pairs from downloaded IAVE exam PDFs.

Ground truth by construction: the marking scheme (_cc.pdf) states the
correct option per item; we never infer an answer, only read it off the
official key. Two marking-scheme formats observed so far:

  table:  "01.   (B)   (C)   11"          (item, v1 answer, v2 answer, points)
  inline: "1. ....... 12 pontos\n(C)"     (item + points, then answer alone)

v1 scope: MCQ items only. Open-response items ("itens de construção") carry
grading rubrics, not direct answers — different extraction problem, left for
a follow-up rather than guessed at here.

Usage: python -m datagen.iave_extract
Writes datagen/iave/extracted.jsonl + datagen/iave/extract-report.json
"""

import json
import re
import subprocess
from pathlib import Path

from datagen.iave_registry import EXAMS

RAW = Path(__file__).parent / "iave" / "raw"

TABLE_ROW_RE = re.compile(
    r"^\s*(\d{1,2}\.\d?\.?)\s+\(([A-Z])\)\s+\(([A-Z])\)\s+(\d+)\s*$", re.MULTILINE)
INLINE_ITEM_RE = re.compile(
    r"^\s*(\d{1,2}\.\d?\.?)\s*(?:\.\s+)?\.{2,}\s*(\d+)\s*pontos?\s*$", re.MULTILINE)
INLINE_ANSWER_RE = re.compile(r"^\s*\(([A-Z])\)\s*$", re.MULTILINE)
VERSAO_ANSWER_RE = re.compile(
    r"Vers[aã]o\s*1\s*[-–]\s*\(([A-Z])\)\s*;\s*Vers[aã]o\s*2\s*[-–]\s*\(([A-Z])\)")


def norm_item(num):
    """Strip leading zeros: CC tables zero-pad ('01.'), exam text doesn't ('1.')."""
    return re.sub(r"^0+(?=\d)", "", num)


def pdf_text(path):
    r = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                       capture_output=True, text=True)
    return r.stdout


def parse_cc_table(text):
    """Filosofia-style: one line per item, both exam-version answers inline."""
    items = {}
    for m in TABLE_ROW_RE.finditer(text):
        num, v1, v2, pts = m.groups()
        items[norm_item(num)] = {"answer_v1": v1, "answer_v2": v2, "points": int(pts)}
    return items


def parse_cc_inline(text):
    """Matematica/FQA-style: item+points on one line, answer within next few lines,
    either a lone (Letter) or 'Versao 1 - (X); Versao 2 - (Y)'."""
    items = {}
    lines = text.split("\n")
    for i, line in enumerate(lines):
        m = INLINE_ITEM_RE.match(line)
        if not m:
            continue
        num, pts = m.groups()
        for j in range(i + 1, min(i + 5, len(lines))):
            vm = VERSAO_ANSWER_RE.search(lines[j])
            if vm:
                items[norm_item(num)] = {"answer_v1": vm.group(1), "answer_v2": vm.group(2),
                                         "points": int(pts)}
                break
            am = INLINE_ANSWER_RE.match(lines[j])
            if am:
                items[norm_item(num)] = {"answer_v1": am.group(1), "answer_v2": None,
                                         "points": int(pts)}
                break
            if lines[j].strip() and not lines[j].strip().startswith("."):
                break  # hit prose (a construction item) before finding a bare letter
    return items


def parse_cc(text):
    items = parse_cc_table(text)
    items.update({k: v for k, v in parse_cc_inline(text).items() if k not in items})
    return items


MCQ_OPTION_RE = re.compile(r"\([A-D]\)")
# Page footer ("Prova 501/1.a F. - Pagina 12/ 15") plus whatever of the next
# page's header bleeds in before the following item's number line - always
# starts with "Prova " + a 3-digit exam code, never part of legitimate prose.
FOOTER_RE = re.compile(r"\s*Prova\s+\d{3}.*", re.DOTALL)


def find_question_text(exam_text, item_num):
    """Text between this item's number-prefixed line and the next, scanning
    ALL occurrences of item_num (not just the first).

    Exams are organized in groups (GRUPO I/II/III, PARTE A/B/C) whose item
    numbering restarts per group, so the same 'item_num' string legitimately
    appears more than once for different (and differently-typed) items.
    Rather than resolve group scoping, we gate on a cheap, high-precision
    safety check: an MCQ item's text must show at least two lettered options.
    We try every occurrence and keep the first one that passes - a real
    answer key attached to a non-MCQ item (wrong group) fails the check and
    is skipped in favour of a later occurrence, rather than shipping a wrong
    ground-truth label.
    """
    pattern = re.compile(
        rf"^\s*{re.escape(item_num)}\s+(.+?)(?=^\s*\d{{1,2}}\.\d?\.?\s|\Z)",
        re.MULTILINE | re.DOTALL)
    for m in pattern.finditer(exam_text):
        q = FOOTER_RE.sub("", m.group(1)).strip()
        q = re.sub(r"\n{2,}", "\n", q).strip()
        if not (10 < len(q) < 3000):
            continue
        if len(MCQ_OPTION_RE.findall(q)) < 2:
            continue
        return q
    return None


# Subjects where notation-heavy items are known to garble under pdftotext's
# math-font handling (verified by manual inspection, not auto-detected -
# see datagen/README or JOURNAL for the specific example). Flagged, not
# discarded: many items in these subjects (combinatorics, geometry-by-figure,
# plain-number problems) extract perfectly cleanly.
NOTATION_RISK_SUBJECTS = {"Matematica A", "Matematica B",
                          "Matematica Aplicada as Ciencias Sociais",
                          "Fisica e Quimica A", "Geometria Descritiva A"}


def main():
    records = []
    report = {"subjects": {}}

    for year, subject, code, phase, exam_url, cc_url in EXAMS:
        exam_pdf = RAW / str(year) / f"{code}_{phase}_exam.pdf"
        cc_pdf = RAW / str(year) / f"{code}_{phase}_cc.pdf"
        if not exam_pdf.exists() or not cc_pdf.exists():
            continue

        cc_text = pdf_text(cc_pdf)
        exam_text = pdf_text(exam_pdf)
        mcq_items = parse_cc(cc_text)

        kept = 0
        for item_num, ans in mcq_items.items():
            q = find_question_text(exam_text, item_num)
            if q is None:
                continue
            records.append({
                "year": year, "subject": subject, "code": code, "phase": phase,
                "item": item_num, "question": q,
                "answer_v1": ans["answer_v1"], "answer_v2": ans["answer_v2"],
                "points": ans["points"],
                "notation_risk": subject in NOTATION_RISK_SUBJECTS,
            })
            kept += 1

        key = f"{subject} ({code})"
        s = report["subjects"].setdefault(key, {"mcq_found": 0, "paired": 0, "sittings": 0})
        s["mcq_found"] += len(mcq_items)
        s["paired"] += kept
        s["sittings"] += 1

    out_dir = Path(__file__).parent / "iave"
    with open(out_dir / "extracted.jsonl", "w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    total_found = sum(s["mcq_found"] for s in report["subjects"].values())
    total_paired = sum(s["paired"] for s in report["subjects"].values())
    report["totals"] = {"mcq_found": total_found, "paired": total_paired,
                        "pair_yield": round(total_paired / total_found, 3) if total_found else 0}
    with open(out_dir / "extract-report.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"{len(records)} question+answer pairs extracted")
    print(f"MCQ items found in marking schemes: {total_found}, paired with question text: {total_paired} "
          f"({report['totals']['pair_yield']:.0%} yield)")
    print("\nper-subject:")
    for subj, s in sorted(report["subjects"].items()):
        y = round(s["paired"] / s["mcq_found"], 2) if s["mcq_found"] else 0
        print(f"  {subj}: {s['sittings']} sittings, {s['mcq_found']} MCQ found, "
              f"{s['paired']} paired ({y:.0%})")


if __name__ == "__main__":
    main()
