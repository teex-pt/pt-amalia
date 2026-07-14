"""Run the pt-PT harness against an Anthropic API model and score with the
same code verifiers as run_harness.py - for comparing against models that
aren't local MLX checkpoints. Same fair-test contract as run_harness.py:
fresh single-turn prompt, no system message, deterministic decoding
(temperature=0), same per-category token budget - the results are directly
comparable, not a different methodology.

This is a benchmarking-only script (send prompts, score responses, report
a number) - it does not use any API model's output as training data for
this project's own models, which is the actual constraint behind this
project's "teacher models must be open" rule.

Usage:
    echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env   # repo root, gitignored
    python -m harness.run_harness_anthropic --model claude-sonnet-5 \
        --label compare-sonnet5 --prompts-file legal_cita_prompts.jsonl

    # --legal-fewshot: a generic grounded-citation system prompt (same
    # rules as this project's production RAG contract - cite with [F#],
    # refuse if uncovered, no claims outside the excerpts - independently
    # worded here, not the literal production prompt) plus one worked
    # example of the [F#] citation format, pulled from legal-v2's TRAINING
    # data (not the eval set, so there's no leakage) - tests whether the
    # gap on legal_cita is closed by instruction+demonstration alone, with
    # zero fine-tuning, or whether it persists.
    python -m harness.run_harness_anthropic --model claude-sonnet-5 \
        --label compare-sonnet5-fewshot --prompts-file legal_cita_prompts.jsonl \
        --legal-fewshot

Writes harness/results-<label>.jsonl and harness/summary-<label>.json,
same schema as run_harness.py.
"""

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from harness.verifiers import CHECKERS

load_dotenv(Path(__file__).parent.parent / ".env")

MAX_TOKENS = {"arithmetic": 60, "format": 300, "variety": 120, "honesty": 150,
              "honesty_control": 150, "mcq": 40, "legal_cita": 400, "legal_refusal": 60}

# Independently worded here (not copied from any production system) -
# same functional rules this project's grounded-citation contract needs:
# answer only from the excerpts, cite with [F#], refuse explicitly if
# uncovered, never cite outside the shown excerpts.
LEGAL_SYSTEM_PROMPT = (
    "És um assistente factual sobre legislação portuguesa. Responde apenas "
    "com base nos EXCERTOS fornecidos, em português europeu. Cada afirmação "
    "tem de citar o excerto que a suporta, no formato [F1], [F2], etc., "
    "indicando sempre o artigo e o diploma de origem. Se os excertos não "
    "contiverem a resposta, diz isso explicitamente em vez de inventar. "
    "Nunca cites um artigo ou diploma que não esteja nos excertos fornecidos."
)

# One worked example from datagen/legal-v2-mix/train.jsonl (training data,
# never in harness/legal_cita_prompts.jsonl) demonstrating the [F#] format.
LEGAL_FEWSHOT_USER = (
    "PERGUNTA: Regula a criação e o regime de organização e funcionamento "
    "dos Centros para a Qualificação e o Ensino Profissional. (CQEP)\n\n"
    "EXCERTOS:\n"
    "[F1] Regime jurídico do Sistema de Regulação de Acesso a Profissões "
    "(SRAP), Artigo 12.º Reconhecimento, validação e certificação de "
    "competências profissionais\n"
    "«1 - O reconhecimento, validação e certificação de competências "
    "profissionais e a correspondente certificação profissional são "
    "assegurados por centros novas oportunidades conjuntamente com "
    "entidades associativas, empresariais, sindicais ou outras, de acordo "
    "com protocolo celebrado para aquele efeito e nos termos da portaria "
    "referida no n.º 2 do artigo 19.º\n"
    "2 - As entidades associativas, empresariais, sindicais ou outras a "
    "que se refere o número anterior devem possuir intervenção e "
    "capacidade reconhecidas nos domínios da actividade ou da "
    "qualificação em que se enquadra o perfil profissional.\n"
    "3 - O reconhecimento, validação e certificação de competências "
    "profissionais desenvolve-se com base nos referenciais de "
    "competências profissionais integrados no CNQ a que se refere o "
    "artigo 6.º do Decreto-Lei n.º 396/2007, de 31 de Dezembro, regulado "
    "pela Portaria n.º 781/2009, de 23 de Julho.»\n"
    "(em vigor desde 2015-04-01)"
)
LEGAL_FEWSHOT_ASSISTANT = (
    "A alteração introduzida por Portaria n.º 135-A/2013, de 2013-03-28, "
    "incide sobre o(s) seguinte(s) ponto(s) do(a) Regime jurídico do "
    "Sistema de Regulação de Acesso a Profissões (SRAP):\n"
    "[F1] Regime jurídico do Sistema de Regulação de Acesso a Profissões "
    "(SRAP), Artigo 12.º Reconhecimento, validação e certificação de "
    "competências profissionais: «1 - O reconhecimento, validação e "
    "certificação de competências profissionais e a correspondente "
    "certificação profissional são assegurados por centros novas "
    "oportunidades conjuntamente com entidades associativas, empresariais, "
    "sindicais ou outras, de acordo com protocolo celebrado para aquele "
    "efeito e nos termos da portaria referida no n.º 2 do artigo 19.º»"
)


def call_with_retry(client, model, prompt, max_tokens, retries=4, system=None, fewshot=False):
    messages = []
    if fewshot:
        messages.append({"role": "user", "content": LEGAL_FEWSHOT_USER})
        messages.append({"role": "assistant", "content": LEGAL_FEWSHOT_ASSISTANT})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(retries):
        try:
            kwargs = {"model": model, "max_tokens": max_tokens, "messages": messages}
            if system:
                kwargs["system"] = system
            resp = client.messages.create(**kwargs)
            return "".join(block.text for block in resp.content if block.type == "text")
        except (anthropic.RateLimitError, anthropic.InternalServerError,
                anthropic.APIConnectionError) as e:
            # transient only - a BadRequestError (bad params/prompt) will
            # never succeed on retry, so don't burn attempts on it.
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  retry {attempt + 1}/{retries} after {type(e).__name__}: {e} (waiting {wait}s)")
            time.sleep(wait)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Anthropic model id, e.g. claude-sonnet-5")
    ap.add_argument("--label", required=True)
    ap.add_argument("--limit", type=int, default=0, help="per-category cap, 0 = all")
    ap.add_argument("--prompts-file", default="prompts.jsonl",
                    help="prompts file inside harness/ (e.g. legal_cita_prompts.jsonl)")
    ap.add_argument("--legal-fewshot", action="store_true",
                    help="prepend a grounded-citation system prompt + one "
                         "training-set worked example of the [F#] format "
                         "(zero fine-tuning, pure in-context)")
    args = ap.parse_args()

    here = Path(__file__).parent
    items = [json.loads(l) for l in open(here / args.prompts_file)]
    if args.limit:
        by_cat = defaultdict(list)
        for i in items:
            if len(by_cat[i["category"]]) < args.limit:
                by_cat[i["category"]].append(i)
        items = [i for cat in by_cat.values() for i in cat]

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    t0 = time.time()
    results, tally = [], defaultdict(lambda: [0, 0])

    system = LEGAL_SYSTEM_PROMPT if args.legal_fewshot else None
    for n, item in enumerate(items, 1):
        text = call_with_retry(client, args.model, item["prompt"], MAX_TOKENS[item["category"]],
                                system=system, fewshot=args.legal_fewshot)
        passed, reason = CHECKERS[item["category"]](item, text.strip())
        tally[item["category"]][0] += passed
        tally[item["category"]][1] += 1
        results.append({**item, "response": text.strip(), "passed": passed, "reason": reason})
        if n % 10 == 0:
            print(f"{n}/{len(items)} done ({time.time() - t0:.0f}s)", flush=True)

    with open(here / f"results-{args.label}.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "label": args.label, "model": args.model,
        "categories": {c: {"passed": p, "total": t, "rate": round(p / t, 3)}
                       for c, (p, t) in sorted(tally.items())},
    }
    summary["overall"] = round(sum(p for p, _ in tally.values()) / len(results), 3)
    with open(here / f"summary-{args.label}.json", "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
