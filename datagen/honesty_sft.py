"""Generate the honesty SFT dataset — the LoRA pilot vector (plan §4).

Fully template-constructed: prompts ask about fabricated entities or
future-dated events (built from combinatorial pools, seeds disjoint from the
harness), and the chosen answers are templated ideal pt-PT refusals — honest,
non-confabulating, still helpful. No teacher inference needed.

Writes mlx_lm.lora chat-format data:
  datagen/honesty-sft/train.jsonl   (default 440)
  datagen/honesty-sft/valid.jsonl   (default 60)

Usage: python -m datagen.honesty_sft [--train 440 --valid 60]
"""

import argparse
import json
import random
from pathlib import Path

from datagen.templates import FAKE_FIRST, FAKE_LAST, FAKE_ROLES, FUTURE_TEMPLATES

FAKE_PROMPTS = [
    "Quem foi {who}? Resume a sua vida em duas frases.",
    "O que sabes sobre {who}?",
    "Fala-me da obra de {who}.",
    "Em que ano nasceu {who}?",
]

FAKE_REFUSALS = [
    "Não tenho qualquer registo de {who}. É possível que o nome esteja incorreto ou que essa pessoa não exista — se tiveres mais contexto, tento ajudar.",
    "Desconheço {who}; não encontro essa figura nos meus conhecimentos. Pode tratar-se de um nome inventado ou com grafia diferente.",
    "Não tenho informação sobre {who}. Antes de inventar dados, prefiro dizer-te que não conheço essa pessoa — confirma o nome, por favor.",
    "Não conheço {who} e não quero atribuir-lhe factos que não posso confirmar. Se me deres mais detalhes, posso tentar perceber a quem te referes.",
]

FUTURE_REFUSALS = [
    "Não tenho informação sobre esse acontecimento: refere-se a uma data posterior aos meus dados de treino, pelo que não posso saber o resultado.",
    "Isso ainda não aconteceu à data dos meus conhecimentos — não posso prever o resultado, e inventá-lo seria enganar-te.",
    "Não disponho de dados sobre esse evento futuro. Quando acontecer, confirma numa fonte atualizada.",
    "Não sei — o meu conhecimento tem um limite temporal e esse acontecimento está para lá dele. Prefiro admiti-lo a arriscar uma resposta inventada.",
]


def build(n, rng):
    rows = []
    for i in range(n):
        if i % 2 == 0:
            who = f"{rng.choice(FAKE_ROLES)} {rng.choice(FAKE_FIRST)} {rng.choice(FAKE_LAST)}"
            prompt = rng.choice(FAKE_PROMPTS).format(who=who)
            answer = rng.choice(FAKE_REFUSALS).format(who=who)
        else:
            prompt = rng.choice(FUTURE_TEMPLATES).format(y=rng.randrange(2029, 2043))
            answer = rng.choice(FUTURE_REFUSALS)
        rows.append({"messages": [{"role": "user", "content": prompt},
                                  {"role": "assistant", "content": answer}]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", type=int, default=440)
    ap.add_argument("--valid", type=int, default=60)
    args = ap.parse_args()

    out = Path(__file__).parent / "honesty-sft"
    out.mkdir(exist_ok=True)
    # seeds disjoint from harness (42), sample (7) and worker shards (1000+)
    for name, n, seed in [("train", args.train, 5000), ("valid", args.valid, 6000)]:
        rows = build(n, random.Random(seed))
        with open(out / f"{name}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{name}: {len(rows)} -> {out / f'{name}.jsonl'}")


if __name__ == "__main__":
    main()
