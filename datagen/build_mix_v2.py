"""Build the pilot-v2 mixed training set (recipe from eval/results/PILOT-honesty-v1.md).

v1 failed the acceptance rule because refusal-only SFT caused arithmetic
interference and over-refusal with template overfit. v2 mixes four slices:

  refusals    templated ideal refusals, EXPANDED template pools (anti-overfit)
  real_qa     on-policy: base AMALIA answers real-entity questions; answers are
              kept only if they pass the no-refusal + keyword gate (anchors the
              model's existing knowledge against over-refusal)
  arithmetic  verified Ministral drafts from a worker shard (anti-interference)
  format      idem

Usage (anchor shard must exist first — see datagen/README.md):
  python -m datagen.worker --role draft --backend mlx \
      --model mlx-community/Ministral-3-14B-Reasoning-2512-4bit \
      --shard 300 --num-shards 1 --per-category 75
  python -m datagen.build_mix_v2 --anchor-shard 300

Writes datagen/mix-v2/{train,valid}.jsonl (mlx_lm.lora chat format).
"""

import argparse
import json
import random
from pathlib import Path

from datagen.templates import FAKE_FIRST, FAKE_LAST, FAKE_ROLES, FUTURE_TEMPLATES
from harness.verifiers import check_honesty_control

FAKE_PROMPTS = [
    "Quem foi {who}? Resume a sua vida em duas frases.",
    "O que sabes sobre {who}?",
    "Fala-me da obra de {who}.",
    "Em que ano nasceu {who}?",
    "Podes fazer uma pequena biografia de {who}?",
    "Qual foi o contributo de {who} para a cultura portuguesa?",
    "Onde viveu {who}?",
    "Diz-me três factos sobre {who}.",
]

FAKE_REFUSALS = [
    "Não tenho qualquer registo de {who}. É possível que o nome esteja incorreto ou que essa pessoa não exista — se tiveres mais contexto, tento ajudar.",
    "Desconheço {who}; não encontro essa figura nos meus conhecimentos. Pode tratar-se de um nome inventado ou com grafia diferente.",
    "Não tenho informação sobre {who}. Antes de inventar dados, prefiro dizer-te que não conheço essa pessoa — confirma o nome, por favor.",
    "Não conheço {who} e não quero atribuir-lhe factos que não posso confirmar. Se me deres mais detalhes, posso tentar perceber a quem te referes.",
    "Esse nome não me diz nada — não tenho registo de {who}. Tens a certeza da grafia?",
    "Procurei nos meus conhecimentos e não encontro {who}. Em vez de arriscar uma biografia inventada, prefiro pedir-te mais contexto.",
    "Não posso confirmar a existência de {who}: não há registo dessa figura naquilo que sei. Se for alguém pouco conhecido, indica-me a área em que trabalhou.",
    "Sinceramente, não sei quem é {who}. Se me disseres onde ouviste o nome, talvez consiga ajudar de outra forma.",
    "{who}? Não reconheço esse nome. Prefiro admitir que não sei a inventar uma resposta.",
    "Não encontro qualquer informação fiável sobre {who}, por isso não vou improvisar uma biografia.",
]

FUTURE_REFUSALS = [
    "Não tenho informação sobre esse acontecimento: refere-se a uma data posterior aos meus dados de treino, pelo que não posso saber o resultado.",
    "Isso ainda não aconteceu à data dos meus conhecimentos — não posso prever o resultado, e inventá-lo seria enganar-te.",
    "Não disponho de dados sobre esse evento futuro. Quando acontecer, confirma numa fonte atualizada.",
    "Não sei — o meu conhecimento tem um limite temporal e esse acontecimento está para lá dele. Prefiro admiti-lo a arriscar uma resposta inventada.",
    "Essa data está no futuro em relação àquilo que sei, por isso qualquer resposta minha seria pura especulação.",
    "Não consigo responder: o evento ainda não tinha acontecido quando os meus dados foram recolhidos. Consulta uma fonte recente.",
    "Boa pergunta, mas está fora do meu alcance temporal — não tenho forma de saber o que aconteceu nessa data.",
    "O meu conhecimento termina antes dessa data. Em vez de inventar um vencedor, digo-te honestamente que não sei.",
    "Não faço previsões nem tenho registo desse acontecimento futuro; recomendo verificares numa fonte atual.",
    "Sobre isso não tenho dados: é posterior ao meu treino. Se precisares, posso explicar o contexto histórico até onde sei.",
]

# Real entities with ultra-canonical verification keywords (any one suffices).
# Held-out control entities from harness/control_prompts.jsonl are NOT here.
REAL_ENTITIES = [
    ("Eça de Queirós", ["escritor", "maias", "romanc"]),
    ("Gil Vicente", ["teatro", "dramaturg", "autos"]),
    ("Florbela Espanca", ["poet", "sonetos"]),
    ("Sophia de Mello Breyner Andresen", ["poet", "contos"]),
    ("Alexandre Herculano", ["escritor", "histor"]),
    ("Almeida Garrett", ["escritor", "teatro", "romantis"]),
    ("Carlos Paredes", ["guitarra", "músic", "compositor"]),
    ("Zeca Afonso", ["grândola", "cantor", "músic"]),
    ("o Marquês de Pombal", ["lisboa", "terramoto", "reconstru", "ministro"]),
    ("o Infante D. Henrique", ["navega", "descobrimentos", "sagres"]),
    ("Fernão de Magalhães", ["circum", "volta ao mundo", "navega"]),
    ("Pedro Álvares Cabral", ["brasil", "navega"]),
    ("Bartolomeu Dias", ["cabo", "boa esperança", "navega"]),
    ("Aristides de Sousa Mendes", ["cônsul", "vistos", "judeus", "guerra"]),
    ("Paula Rego", ["pint", "artista"]),
    ("Álvaro Siza Vieira", ["arquitet"]),
    ("Maria João Pires", ["pian"]),
    ("Eusébio", ["futebol", "benfica", "pantera"]),
    ("Rosa Mota", ["marat", "atlet", "corr"]),
    ("Luís Figo", ["futebol", "jogador"]),
    ("José Mourinho", ["treinador", "futebol"]),
    ("a Batalha de Aljubarrota", ["1385", "castela", "batalha", "independência"]),
    ("o Tratado de Tordesilhas", ["castela", "divis", "1494", "espanha"]),
    ("o Estado Novo", ["salazar", "ditadura", "regime"]),
    ("a Grândola Vila Morena", ["zeca", "canção", "revolução", "abril", "senha"]),
    ("o rio Douro", ["porto", "vinho", "rio", "espanha"]),
    ("a Serra da Estrela", ["montanha", "mais alta", "queijo", "serra"]),
    ("os Açores", ["arquipélago", "ilhas", "atlântico"]),
    ("a ilha da Madeira", ["ilha", "funchal", "atlântico"]),
    ("Sintra", ["palácio", "património", "vila", "serra"]),
    ("Óbidos", ["vila", "muralha", "castelo", "ginja"]),
    ("a Universidade de Coimbra", ["1290", "antiga", "universidade", "estudant"]),
    ("o Santuário de Fátima", ["santuário", "peregrin", "aparições", "religios"]),
    ("o Mosteiro dos Jerónimos", ["lisboa", "manuelino", "mosteiro", "belém"]),
    ("a Ponte 25 de Abril", ["lisboa", "ponte", "tejo"]),
    ("o caldo verde", ["sopa", "couve", "chouriço"]),
    ("a francesinha", ["porto", "sandu", "molho", "prato"]),
    ("o vinho do Porto", ["douro", "vinho", "fortificado", "doce"]),
    ("o vinho verde", ["minho", "vinho", "fresco"]),
    ("o galo de Barcelos", ["lenda", "símbolo", "barro", "milagre"]),
    ("a língua mirandesa", ["mirand", "língua", "oficial"]),
    ("Guimarães", ["berço", "primeiro rei", "castelo", "nação"]),
    ("Évora", ["alentejo", "templo", "romano", "património"]),
    ("Braga", ["minho", "bom jesus", "igrejas", "romana"]),
    ("o Parque Nacional da Peneda-Gerês", ["parque", "nacional", "natureza", "gerês"]),
    ("Almada Negreiros", ["modernis", "pint", "futuris", "artista"]),
]

REAL_PROMPTS = ["Quem foi {who}?", "O que sabes sobre {who}?",
                "Fala-me sobre {who} em duas ou três frases.",
                "Porque é que {who} é importante para Portugal?"]
PLACE_PROMPTS = ["O que é {who}?", "O que sabes sobre {who}?",
                 "Fala-me sobre {who} em duas ou três frases.",
                 "Porque é que {who} é importante para Portugal?"]


def build_refusals(n, rng):
    rows = []
    for i in range(n):
        if i % 2 == 0:
            who = f"{rng.choice(FAKE_ROLES)} {rng.choice(FAKE_FIRST)} {rng.choice(FAKE_LAST)}"
            q = rng.choice(FAKE_PROMPTS).format(who=who)
            a = rng.choice(FAKE_REFUSALS).format(who=who)
        else:
            q = rng.choice(FUTURE_TEMPLATES).format(y=rng.randrange(2029, 2043))
            a = rng.choice(FUTURE_REFUSALS)
        rows.append({"messages": [{"role": "user", "content": q},
                                  {"role": "assistant", "content": a}],
                     "slice": "refusals"})
    return rows


def build_real_qa(rng, model_path):
    """On-policy: base AMALIA answers; keep only gated answers."""
    import mlx.core as mx
    from mlx_lm import load, stream_generate
    try:
        mx.set_memory_limit(14 * 1024**3)
    except Exception:
        pass
    model, tokenizer = load(model_path)

    rows, rejected = [], 0
    for who, keys in REAL_ENTITIES:
        pool = PLACE_PROMPTS if who[0].islower() or who.startswith(("a ", "o ", "os ", "as ")) else REAL_PROMPTS
        for q_t in rng.sample(pool, 2):
            q = q_t.format(who=who)
            ids = tokenizer.apply_chat_template(
                [{"role": "user", "content": q}], add_generation_prompt=True)
            text = ""
            for r in stream_generate(model, tokenizer, ids, max_tokens=180):
                text += r.text
            mx.clear_cache()
            ok, _ = check_honesty_control({"must_contain": keys}, text.strip())
            if ok:
                rows.append({"messages": [{"role": "user", "content": q},
                                          {"role": "assistant", "content": text.strip()}],
                             "slice": "real_qa"})
            else:
                rejected += 1
    print(f"real_qa: kept {len(rows)}, gated out {rejected}", flush=True)
    del model, tokenizer
    mx.clear_cache()
    return rows


def load_anchor(shard):
    out_dir = Path(__file__).parent / "out"
    rows = []
    for f in out_dir.glob(f"shard-{shard:03d}-draft-*.jsonl"):
        for line in open(f):
            r = json.loads(line)
            if r["verifier"]["passed"]:
                rows.append({"messages": [{"role": "user", "content": r["prompt"]},
                                          {"role": "assistant", "content": r["final"]}],
                             "slice": r["category"]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor-shard", type=int, default=300)
    ap.add_argument("--refusals", type=int, default=300)
    ap.add_argument("--model", default="./amalia-mlx-8bit")
    args = ap.parse_args()

    rng = random.Random(7000)
    refusals = build_refusals(args.refusals, rng)
    anchor = load_anchor(args.anchor_shard)
    real_qa = build_real_qa(rng, args.model)

    rows = refusals + anchor + real_qa
    rng.shuffle(rows)
    n_valid = max(40, len(rows) // 12)
    out = Path(__file__).parent / "mix-v2"
    out.mkdir(exist_ok=True)
    for name, chunk in [("valid", rows[:n_valid]), ("train", rows[n_valid:])]:
        with open(out / f"{name}.jsonl", "w") as f:
            for r in chunk:
                f.write(json.dumps({"messages": r["messages"]}, ensure_ascii=False) + "\n")
    from collections import Counter
    print("mix:", dict(Counter(r["slice"] for r in rows)),
          f"-> train {len(rows) - n_valid}, valid {n_valid}")


if __name__ == "__main__":
    main()
