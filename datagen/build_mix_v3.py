"""Build the pilot-v3 training mix (plan: eval/results/PILOT-honesty-v3-PLAN.md).

Slices (~750 samples):
  refusals   200  expanded pools (14 fake + 14 future templates)
  real_qa    150  on-policy gated answers, entity pool 46 -> 80
  boundary   120  NEW: near-twin pairs — real entity (answer) vs surname-mutated
                  fake twin (refusal). Teaches the boundary, not the pattern.
  arith_r    180  arithmetic anchors WITH one-line reasoning (Ministral, verified)
  format     100  format anchors from worker shard 301

Requires shard 301 to exist:
  python -m datagen.worker --role draft --backend mlx \
      --model mlx-community/Ministral-3-14B-Reasoning-2512-4bit \
      --shard 301 --num-shards 1 --per-category 100 --categories format

Usage: python -m datagen.build_mix_v3
Writes datagen/mix-v3/{train,valid}.jsonl. All prompts are checked for exact
overlap against the evaluation files before writing (hard fail on collision).
"""

import argparse
import gc
import json
import random
import re
from pathlib import Path

from datagen.build_mix_v2 import (FAKE_PROMPTS, FAKE_REFUSALS, FUTURE_REFUSALS,
                                  REAL_ENTITIES, REAL_PROMPTS, PLACE_PROMPTS)
from datagen.templates import (FAKE_FIRST, FAKE_LAST, FAKE_ROLES,
                               FUTURE_TEMPLATES, arithmetic_items)
from harness.verifiers import CHECKERS, check_honesty_control

THINK_RE = re.compile(r"\[THINK\].*?\[/THINK\]|<think>.*?</think>", re.DOTALL)

FAKE_REFUSALS_V3 = FAKE_REFUSALS + [
    "Fiz uma busca no que sei e {who} não aparece em lado nenhum. Diz-me mais alguma coisa sobre o contexto?",
    "Receio não poder ajudar: {who} não consta dos meus conhecimentos e inventar uma biografia seria pior do que admitir isso.",
    "Hmm, esse nome é-me completamente desconhecido. Não vou arriscar detalhes sobre {who} sem qualquer base.",
    "Não identifico {who}. Se for uma figura regional ou pouco documentada, indica-me a área e a época e tento ajudar com o contexto.",
]
FUTURE_REFUSALS_V3 = FUTURE_REFUSALS + [
    "Pergunta-me sobre esse evento depois de acontecer — à data do meu treino ainda não tinha ocorrido.",
    "Isso pertence ao futuro em relação ao meu conhecimento; não existe ainda resposta que eu possa dar com honestidade.",
    "Sem bola de cristal: esse acontecimento está para lá do meu limite temporal e não vou inventar o desfecho.",
    "A minha informação termina antes dessa data; sugiro confirmares numa fonte noticiosa atual.",
]

EXTRA_ENTITIES = [
    ("Fernão Lopes", ["cronista", "crónica"]), ("Damião de Góis", ["humanista", "cronista"]),
    ("o rei D. Manuel I", ["manuelino", "descobrimentos", "rei"]),
    ("José Régio", ["poeta", "presença", "escritor"]), ("Vergílio Ferreira", ["escritor", "romanc", "aparição"]),
    ("Eugénio de Andrade", ["poeta", "poesia"]), ("Natália Correia", ["poet", "escritora"]),
    ("Amadeo de Souza-Cardoso", ["pint", "modernis"]), ("Maria Helena Vieira da Silva", ["pint", "abstra"]),
    ("Júlio Pomar", ["pint", "artista"]), ("António Variações", ["músic", "cantor", "pop"]),
    ("Rui Veloso", ["rock", "músic", "cantor"]), ("os Madredeus", ["grupo", "músic", "banda"]),
    ("Carlos do Carmo", ["fado", "fadista", "cantor"]), ("Herman José", ["humor", "televis"]),
    ("Raul Solnado", ["humor", "ator", "comediante"]), ("Eunice Muñoz", ["atriz", "teatro"]),
    ("Nicolau Breyner", ["ator", "televis"]), ("Vítor Baía", ["guarda-redes", "porto", "futebol"]),
    ("Paulo Futre", ["futebol", "atlético", "jogador"]), ("Carlos Lopes", ["marat", "olímpic", "ouro"]),
    ("Joaquim Agostinho", ["ciclis", "volta"]), ("Calouste Gulbenkian", ["fundação", "mecenas", "petróleo"]),
    ("o Chiado", ["lisboa", "bairro", "incêndio"]), ("o Castelo de São Jorge", ["lisboa", "castelo", "colina"]),
    ("o Palácio de Queluz", ["palácio", "rococó", "queluz"]),
    ("o Aqueduto das Águas Livres", ["aqueduto", "lisboa", "água"]),
    ("o vinho da Madeira", ["madeira", "vinho", "fortificado"]),
    ("a amêijoa à Bulhão Pato", ["amêijoa", "coentros", "marisco", "prato"]),
    ("o cozido à portuguesa", ["prato", "carnes", "enchidos", "couves"]),
    ("as Janeiras", ["cantar", "janeiro", "tradição"]),
    ("o fado de Coimbra", ["fado", "coimbra", "estudant"]),
    ("o São Martinho", ["castanhas", "novembro", "magusto"]),
    ("a Queima das Fitas", ["estudant", "coimbra", "festa"]),
]
ALL_ENTITIES = REAL_ENTITIES + EXTRA_ENTITIES  # 80

# surname pools for boundary twins — disjoint from the eval-only pools
MUT_LAST = ["Vasconcelos de Aguiar", "Castelo de Mesão Frio", "Alvim de Panóias",
            "Sequeira do Vouga", "Tavares de Alpedrinha", "Noronha de Cambra",
            "Guedes de Sortelha Velha", "Abrantes do Sabugal", "Vilhena de Odemira",
            "Fontoura de Basto"]


def is_person(name):
    return not (name[0].islower() or name.split()[0] in ("o", "a", "os", "as"))


def build_refusals(n, rng):
    rows = []
    for i in range(n):
        if i % 2 == 0:
            who = f"{rng.choice(FAKE_ROLES)} {rng.choice(FAKE_FIRST)} {rng.choice(FAKE_LAST)}"
            q = rng.choice(FAKE_PROMPTS).format(who=who)
            a = rng.choice(FAKE_REFUSALS_V3).format(who=who)
        else:
            q = rng.choice(FUTURE_TEMPLATES).format(y=rng.randrange(2029, 2043))
            a = rng.choice(FUTURE_REFUSALS_V3)
        rows.append({"messages": [{"role": "user", "content": q},
                                  {"role": "assistant", "content": a}], "slice": "refusals"})
    return rows


def reasoned_arithmetic(n, rng, backend):
    items = arithmetic_items(n, rng, "v3r")
    rows, kept = [], 0
    for i, it in enumerate(items, 1):
        prompt = re.sub(r"Responde apenas com [^.]+\.",
                        "Explica o cálculo numa única linha e termina com a resposta.",
                        it["prompt"])
        raw = backend.generate(prompt, 2048)
        final = THINK_RE.sub("", raw).strip()
        ok, _ = CHECKERS["arithmetic"]({**it, "max_words": 45}, final)
        if ok:
            kept += 1
            rows.append({"messages": [{"role": "user", "content": prompt},
                                      {"role": "assistant", "content": final}],
                         "slice": "arith_reasoned"})
        if i % 20 == 0:
            print(f"arith_reasoned {i}/{n} (kept {kept})", flush=True)
    return rows


def onpolicy_answers(questions, backend):
    """questions: list of (prompt, gate_keys or None). Returns gated rows."""
    rows = []
    for q, keys in questions:
        text = backend.generate(q, 180)
        if keys is None or check_honesty_control({"must_contain": keys}, text)[0]:
            rows.append((q, text))
    return rows


class MLX:
    def __init__(self, path):
        import mlx.core as mx
        from mlx_lm import load, stream_generate
        try:
            mx.set_memory_limit(14 * 1024**3)
        except Exception:
            pass
        self.mx, self.stream = mx, stream_generate
        self.model, self.tok = load(path, tokenizer_config={"fix_mistral_regex": True})

    def generate(self, prompt, max_tokens):
        ids = self.tok.apply_chat_template(
            [{"role": "user", "content": prompt}], add_generation_prompt=True)
        text = ""
        for r in self.stream(self.model, self.tok, ids, max_tokens=max_tokens):
            text += r.text
        self.mx.clear_cache()
        return text.strip()

    def unload(self):
        del self.model, self.tok
        gc.collect()
        self.mx.clear_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teacher", default="mlx-community/Ministral-3-14B-Reasoning-2512-4bit")
    ap.add_argument("--student", default="./amalia-mlx-8bit")
    ap.add_argument("--format-shard", type=int, default=301)
    args = ap.parse_args()
    here = Path(__file__).parent
    rng = random.Random(7300)

    # ---- slice 1: refusals (no model) ----
    rows = build_refusals(200, rng)

    # ---- slice 2: format anchors from worker shard ----
    n_fmt = 0
    for f in (here / "out").glob(f"shard-{args.format_shard:03d}-draft-*.jsonl"):
        for line in open(f):
            r = json.loads(line)
            if r["category"] == "format" and r["verifier"]["passed"] and n_fmt < 100:
                n_fmt += 1
                rows.append({"messages": [{"role": "user", "content": r["prompt"]},
                                          {"role": "assistant", "content": r["final"]}],
                             "slice": "format"})
    print(f"format anchors: {n_fmt}", flush=True)

    # ---- slice 3: reasoned arithmetic (Ministral) ----
    teacher = MLX(args.teacher)
    rows += reasoned_arithmetic(180, rng, teacher)
    teacher.unload()

    # ---- slices 4+5: real-QA and boundary pairs (AMALIA on-policy) ----
    student = MLX(args.student)
    real_qs = []
    for who, keys in ALL_ENTITIES:
        pool = PLACE_PROMPTS if not is_person(who) else REAL_PROMPTS
        for t in rng.sample(pool, 2):
            real_qs.append((t.format(who=who), keys))
    kept = onpolicy_answers(real_qs, student)[:150]
    rows += [{"messages": [{"role": "user", "content": q},
                           {"role": "assistant", "content": a}], "slice": "real_qa"}
             for q, a in kept]
    print(f"real_qa kept: {len(kept)}/{len(real_qs)}", flush=True)

    people = [(w, k) for w, k in ALL_ENTITIES if is_person(w)]
    pairs = rng.sample(people, min(60, len(people)))
    n_b = 0
    for who, keys in pairs:
        parts = who.split()
        first = parts[1] if parts[0] in ("o", "a") and len(parts) > 2 else parts[0]
        twin = f"{first} {rng.choice(MUT_LAST)}"
        q_real = f"Quem foi {who}? Responde em duas ou três frases."
        ans = onpolicy_answers([(q_real, keys)], student)
        if ans:
            rows.append({"messages": [{"role": "user", "content": q_real},
                                      {"role": "assistant", "content": ans[0][1]}],
                         "slice": "boundary_real"})
            q_fake = f"Quem foi {twin}? Responde em duas ou três frases."
            rows.append({"messages": [{"role": "user", "content": q_fake},
                                      {"role": "assistant",
                                       "content": rng.choice(FAKE_REFUSALS_V3).format(who=twin)}],
                         "slice": "boundary_fake"})
            n_b += 2
    print(f"boundary pairs: {n_b} rows", flush=True)
    student.unload()

    # ---- collision check against evaluation files (hard fail) ----
    eval_prompts = set()
    for fname in ("prompts.jsonl", "prompts-extended.jsonl",
                  "control_prompts.jsonl", "control_prompts_v3.jsonl"):
        fp = here.parent / "harness" / fname
        if fp.exists():
            eval_prompts |= {json.loads(l)["prompt"] for l in open(fp)}
    collisions = [r for r in rows if r["messages"][0]["content"] in eval_prompts]
    assert not collisions, f"TRAIN/EVAL COLLISION: {len(collisions)} prompts overlap!"

    rng.shuffle(rows)
    n_valid = max(50, len(rows) // 12)
    out = here / "mix-v3"
    out.mkdir(exist_ok=True)
    for name, chunk in [("valid", rows[:n_valid]), ("train", rows[n_valid:])]:
        with open(out / f"{name}.jsonl", "w") as f:
            for r in chunk:
                f.write(json.dumps({"messages": r["messages"]}, ensure_ascii=False) + "\n")
    from collections import Counter
    print("mix-v3:", dict(Counter(r["slice"] for r in rows)),
          f"-> train {len(rows) - n_valid}, valid {n_valid}")


if __name__ == "__main__":
    main()
