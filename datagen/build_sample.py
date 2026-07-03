"""Smoke test for the two-stage synthetic data pipeline (plan §3).

Builds a small sample (4 items per category) end-to-end to validate the flow:

  stage 1 (content):  Ministral-3-14B-Reasoning drafts arithmetic/format answers
                      ([THINK] traces stripped but preserved for Path A);
  stage 2 (surface):  a pt-PT rewriter (AMALIA by default, EuroLLM when available)
                      renders drafts into European Portuguese;
  honesty:            on-policy — AMALIA answers directly; the verifier verdict
                      splits chosen/rejected DPO candidates;
  variety:            pt-BR sentences rewritten by the rewriter directly;
  gate:               harness verifiers run on the FINAL text of every record.

Models are loaded strictly one at a time (Mac-safe). Usage:

  python -m datagen.build_sample --rewriter amalia
  python -m datagen.build_sample --rewriter eurollm   # after conversion exists

Output: datagen/sample/sample-<rewriter>.jsonl + printed pass-rate report.
"""

import argparse
import gc
import json
import random
import re
from pathlib import Path

import mlx.core as mx

try:
    mx.set_memory_limit(24 * 1024**3)
    mx.set_wired_limit(20 * 1024**3)
except Exception:
    pass

from mlx_lm import load, stream_generate

from harness.verifiers import CHECKERS, find_br_markers

TEACHER = "mlx-community/Ministral-3-14B-Reasoning-2512-4bit"
REWRITERS = {
    "amalia": "./amalia-mlx-8bit",
    "eurollm": "./eurollm-22b-mlx-4bit",
}
THINK_RE = re.compile(r"\[THINK\].*?\[/THINK\]|<think>.*?</think>", re.DOTALL)

R = random.Random(7)  # different seed from the harness — no eval overlap


def make_items():
    """Four verifiable items per category, ground truth by construction."""
    items = []
    for i in range(4):
        h, m, dh, dm = R.randrange(6, 20), R.choice([10, 25, 40]), R.randrange(1, 4), R.choice([15, 35, 50])
        items.append({
            "id": f"arithmetic-{i}", "category": "arithmetic", "subtype": "time",
            "prompt": f"Um autocarro parte às {h}h{m:02d} e a viagem demora {dh} horas e {dm} minutos. "
                      f"A que horas chega? Responde apenas com a hora, no formato HHhMM.",
            "answer": [(h + dh + (m + dm) // 60) % 24, (m + dm) % 60], "max_words": 8,
        })
    for i, (count, keys, topic) in enumerate([
        (3, ["nome", "distrito"], "praias portuguesas"),
        (4, ["nome", "epoca"], "festas tradicionais portuguesas"),
        (3, ["titulo", "autor"], "romances portugueses do século XIX"),
        (4, ["nome", "regiao"], "vinhos portugueses"),
    ]):
        items.append({
            "id": f"format-{i}", "category": "format", "subtype": "json_array",
            "prompt": f"Lista exatamente {count} {topic} em JSON: responde apenas com um array "
                      f"(sem objeto raiz) de {count} objetos, cada um apenas com os campos "
                      f"\"{keys[0]}\" e \"{keys[1]}\".",
            "count": count, "keys": keys,
        })
    for i, (sent, keep) in enumerate([
        ("Você esqueceu o celular no banheiro do escritório.", ["escritório"]),
        ("A gente está esperando o ônibus há meia hora.", ["meia hora"]),
        ("O time está treinando para o campeonato que começa semana que vem.", ["campeonato"]),
        ("Ela está dirigindo para o aeroporto porque o voo sai às sete.", ["aeroporto", "sete"]),
    ]):
        items.append({
            "id": f"variety-{i}", "category": "variety", "subtype": "rewrite",
            "prompt": f"Reescreve a frase seguinte em português europeu: «{sent}» "
                      f"Responde apenas com a frase reescrita.",
            "must_keep": keep,
        })
    for i, q in enumerate([
        "Quem foi a escritora portuguesa Matilde Serrão de Alcobaça? Resume a sua vida em duas frases.",
        "O que estabelece o Decreto-Lei n.º 612/1987 sobre a apicultura transmontana?",
        "Quem venceu a Taça de Portugal de futebol em 2033?",
        "Qual foi o resultado do referendo português de 2034?",
    ]):
        items.append({"id": f"honesty-{i}", "category": "honesty",
                      "subtype": "fake_or_future", "prompt": q})
    return items


def generate(model, tokenizer, prompt, max_tokens):
    ids = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], add_generation_prompt=True)
    text = ""
    for r in stream_generate(model, tokenizer, ids, max_tokens=max_tokens):
        text += r.text
    mx.clear_cache()
    return text.strip()


def unload(model, tokenizer):
    del model, tokenizer
    gc.collect()
    mx.clear_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rewriter", choices=list(REWRITERS), default="amalia")
    args = ap.parse_args()
    rewriter_path = REWRITERS[args.rewriter]

    items = make_items()
    records = {i["id"]: {**i, "provenance": {"template": i["subtype"]}} for i in items}

    # ---- stage 1: teacher drafts for arithmetic + format --------------------
    print(f"[stage 1] loading teacher {TEACHER}", flush=True)
    model, tokenizer = load(TEACHER, tokenizer_config={"fix_mistral_regex": True})
    for it in items:
        if it["category"] not in ("arithmetic", "format"):
            continue
        raw = generate(model, tokenizer, it["prompt"], max_tokens=2048)
        trace = THINK_RE.findall(raw)
        draft = THINK_RE.sub("", raw).strip()
        rec = records[it["id"]]
        rec["provenance"].update(teacher=TEACHER, trace=trace[0] if trace else None)
        rec["draft"] = draft
        print(f"  drafted {it['id']} ({len(draft)} chars)", flush=True)
    unload(model, tokenizer)

    # ---- stage 2: rewriter renders pt-PT; also on-policy honesty + variety --
    print(f"[stage 2] loading rewriter {rewriter_path}", flush=True)
    model, tokenizer = load(rewriter_path)
    for it in items:
        rec = records[it["id"]]
        if it["category"] in ("arithmetic", "format"):
            # verify-early: a draft that already passes (and is pt-BR-clean)
            # needs no rewrite — rewriting a correct answer can only break it
            ok, _ = CHECKERS[it["category"]](it, rec["draft"])
            if ok and not find_br_markers(rec["draft"]):
                rec["final"] = rec["draft"]
                rec["provenance"]["rewriter"] = None
                rec["provenance"]["draft_passed"] = True
                print(f"  {it['id']}: draft passed, rewrite skipped", flush=True)
                continue
            rewrite_prompt = (
                "Reescreve a resposta seguinte em português europeu correto, mantendo "
                "exatamente os números, a estrutura e o formato. Responde apenas com a "
                f"resposta reescrita.\n\nPergunta: {it['prompt']}\n\nResposta: {rec['draft']}")
            rec["final"] = generate(model, tokenizer, rewrite_prompt, max_tokens=400)
            rec["provenance"]["rewriter"] = rewriter_path
        else:  # variety rewrite and on-policy honesty go straight to this model
            rec["final"] = generate(model, tokenizer, it["prompt"], max_tokens=200)
            rec["provenance"]["rewriter"] = None
            rec["provenance"]["on_policy_model"] = rewriter_path
        print(f"  finalized {it['id']}", flush=True)
    unload(model, tokenizer)

    # ---- gate: verifiers on the final text ----------------------------------
    out_dir = Path(__file__).parent / "sample"
    out_dir.mkdir(exist_ok=True)
    passed_by_cat, out_path = {}, out_dir / f"sample-{args.rewriter}.jsonl"
    with open(out_path, "w") as f:
        for it in items:
            rec = records[it["id"]]
            ok, reason = CHECKERS[it["category"]](it, rec["final"])
            rec["verifier"] = {"passed": ok, "reason": reason}
            rec["disposition"] = (
                "sft" if ok and it["category"] != "honesty"
                else "dpo_chosen" if ok
                else "dpo_rejected" if it["category"] == "honesty" or "draft" in rec
                else "discard")
            passed_by_cat.setdefault(it["category"], []).append(ok)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\nwrote {out_path}")
    for cat, oks in sorted(passed_by_cat.items()):
        print(f"  {cat}: {sum(oks)}/{len(oks)} passed verification")
    print("pipeline smoke test complete — inspect the jsonl before scaling up")


if __name__ == "__main__":
    main()
