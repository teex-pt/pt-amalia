"""Seeded, shardable prompt templates with ground truth by construction.

Each shard derives its own RNG (seed = 1000 + shard); the harness uses seed 42
and the smoke sample seed 7, so generated data never overlaps the eval prompts.
Final dedup against harness/benchmarks happens again in merge_shards.py.
"""

import random

CITIES = ["Lisboa", "Porto", "Coimbra", "Braga", "Faro", "Évora", "Aveiro",
          "Viseu", "Guarda", "Leiria", "Setúbal", "Viana do Castelo", "Beja",
          "Bragança", "Castelo Branco", "Portalegre", "Santarém", "Vila Real"]

JSON_TOPICS = [
    (["nome", "distrito"], "rios portugueses"), (["nome", "distrito"], "praias portuguesas"),
    (["nome", "seculo"], "escritores portugueses"), (["nome", "regiao"], "queijos portugueses"),
    (["cidade", "monumento"], "monumentos nacionais"), (["nome", "capital"], "países da União Europeia"),
    (["nome", "epoca"], "festas tradicionais portuguesas"), (["nome", "regiao"], "vinhos portugueses"),
    (["ilha", "arquipelago"], "ilhas portuguesas"), (["nome", "ano"], "clubes de futebol portugueses e o ano da fundação"),
    (["prato", "regiao"], "pratos tradicionais portugueses"), (["nome", "distrito"], "serras de Portugal"),
]

WC_TOPICS = ["o fado", "o rio Tejo", "a cidade do Porto", "os pastéis de nata",
             "o azulejo", "a Serra da Estrela", "o galo de Barcelos", "o vinho do Porto",
             "a Torre de Belém", "o bacalhau", "a guitarra portuguesa", "as vindimas"]

NUM_TOPICS = ["vantagens de andar de bicicleta", "capitais de distrito", "frutas de outono",
              "razões para aprender português", "provérbios portugueses", "profissões tradicionais",
              "aves comuns em Portugal", "danças folclóricas", "doces conventuais"]

BR_SENTENCES = [
    ("Você vai pegar o ônibus para o trabalho amanhã de manhã.", ["trabalho", "amanhã"]),
    ("Meu celular ficou sem bateria durante o café da manhã.", ["bateria"]),
    ("A gente vai comprar sorvete depois do treino.", ["treino"]),
    ("O banheiro do apartamento está sendo reformado.", ["apartamento"]),
    ("Ela está esperando o trem na estação há vinte minutos.", ["estação", "vinte"]),
    ("Coloca o suco na geladeira antes que esquente.", ["antes"]),
    ("Vamos atravessar na faixa de pedestre perto do ponto de ônibus.", ["atravessar", "perto"]),
    ("Você está dirigindo muito rápido nesta estrada.", ["estrada"]),
    ("Estou fazendo um bolo para o aniversário da minha filha.", ["bolo", "filha"]),
    ("Vocês estão planejando as férias para julho?", ["férias", "julho"]),
    ("Ele está morando num apartamento perto do centro.", ["centro"]),
    ("O encanador está consertando a pia da cozinha.", ["cozinha"]),
    ("Ela está dirigindo para o aeroporto porque o voo sai às sete.", ["aeroporto", "sete"]),
    ("O caminhão de mudanças está estacionando na frente do prédio.", ["prédio"]),
]

GEN_TOPICS = ["a vindima no Douro", "uma ida à praia", "o mercado municipal",
              "uma viagem de metro", "o Natal em família", "um jogo no estádio",
              "uma tarde na biblioteca", "a apanha da azeitona", "um passeio de elétrico",
              "as festas de São João", "um jantar de aniversário", "a época de exames",
              "uma caminhada na serra", "um dia de chuva", "as compras da semana"]

FAKE_FIRST = ["Aurélio", "Matilde", "Duarte", "Leonor", "Vasco", "Beatriz", "Artur", "Urraca", "Gaspar", "Iria"]
FAKE_LAST = ["Vasconcelos de Mirandela", "Serrão de Alcobaça", "Peixoto de Alvarenga",
             "Bragança Ataíde", "Teles de Miranda", "Bandeira Quintela", "Camelo dos Anjos",
             "Sarmento de Vilariça", "Botelho de Sernancelhe", "Coutinho de Arraiolos"]
FAKE_ROLES = ["o poeta português", "a fadista", "o navegador", "a escritora", "o pintor",
              "o cientista português", "a compositora", "o arquiteto"]

FUTURE_TEMPLATES = [
    "Quem venceu o Festival Eurovisão da Canção de {y}?",
    "Quem ganhou o Campeonato do Mundo de futebol de {y}?",
    "Qual foi o resultado das eleições legislativas portuguesas de {y}?",
    "Quem recebeu o Prémio Nobel da Literatura em {y}?",
    "Que cidade foi Capital Europeia da Cultura em {y}?",
    "Quem venceu a Volta a Portugal em bicicleta de {y}?",
    "Qual era a população de Portugal no censo de {y}?",
    "Quem foi eleito Presidente da República Portuguesa em {y}?",
]


def arithmetic_items(n, rng, prefix):
    items = []
    for i in range(n):
        kind = ("time", "money", "percent")[i % 3]
        if kind == "time":
            h, m = rng.randrange(5, 21), rng.choice(range(0, 60, 5))
            dh, dm = rng.randrange(1, 6), rng.choice(range(5, 60, 5))
            a, b = rng.sample(CITIES, 2)
            items.append({
                "id": f"{prefix}-arithmetic-{i:04d}", "category": "arithmetic", "subtype": "time",
                "prompt": f"Um comboio parte de {a} às {h}h{m:02d} e demora {dh} horas e {dm} minutos "
                          f"a chegar a {b}. A que horas chega? Responde apenas com a hora, no formato HHhMM.",
                "answer": [(h + dh + (m + dm) // 60) % 24, (m + dm) % 60], "max_words": 8})
        elif kind == "money":
            p1, p2 = rng.randrange(4, 90), rng.randrange(3, 60)
            disc = rng.choice([10, 15, 20, 25, 30, 50])
            items.append({
                "id": f"{prefix}-arithmetic-{i:04d}", "category": "arithmetic", "subtype": "money",
                "prompt": f"Compras um artigo de {p1} euros e outro de {p2} euros, com um desconto de "
                          f"{disc}% sobre o total. Quanto pagas? Responde apenas com o valor em euros.",
                "answer": round((p1 + p2) * (1 - disc / 100), 2), "max_words": 8})
        else:
            base = rng.choice([40, 60, 80, 120, 150, 200, 240, 300, 360, 480, 600])
            pct = rng.choice([5, 10, 15, 20, 25, 30, 40, 60, 75])
            items.append({
                "id": f"{prefix}-arithmetic-{i:04d}", "category": "arithmetic", "subtype": "percent",
                "prompt": f"Numa escola com {base} alunos, {pct}% estudam alemão. Quantos alunos "
                          f"estudam alemão? Responde apenas com o número.",
                "answer": base * pct / 100, "max_words": 6})
    return items


def format_items(n, rng, prefix):
    items = []
    for i in range(n):
        kind = ("json_array", "word_count", "numbered_items")[i % 3]
        if kind == "json_array":
            keys, topic = rng.choice(JSON_TOPICS)
            count = rng.randrange(3, 7)
            items.append({
                "id": f"{prefix}-format-{i:04d}", "category": "format", "subtype": "json_array",
                "prompt": f"Lista exatamente {count} {topic} em JSON: responde apenas com um array "
                          f"(sem objeto raiz) de {count} objetos, cada um apenas com os campos "
                          f"\"{keys[0]}\" e \"{keys[1]}\".", "count": count, "keys": keys})
        elif kind == "word_count":
            topic, wc = rng.choice(WC_TOPICS), rng.randrange(7, 14)
            items.append({
                "id": f"{prefix}-format-{i:04d}", "category": "format", "subtype": "word_count",
                "prompt": f"Escreve uma frase sobre {topic} com exatamente {wc} palavras. "
                          f"Responde apenas com a frase.", "count": wc})
        else:
            topic = rng.choice(NUM_TOPICS)
            count, mw = rng.randrange(3, 6), rng.randrange(4, 8)
            items.append({
                "id": f"{prefix}-format-{i:04d}", "category": "format", "subtype": "numbered_items",
                "prompt": f"Lista exatamente {count} {topic}, em linhas numeradas (1., 2., ...), "
                          f"cada uma com no máximo {mw} palavras. Responde apenas com a lista.",
                "count": count, "max_words": mw})
    return items


def variety_items(n, rng, prefix):
    items = []
    for i in range(n):
        if i % 2 == 0:
            sent, keep = rng.choice(BR_SENTENCES)
            items.append({
                "id": f"{prefix}-variety-{i:04d}", "category": "variety", "subtype": "rewrite",
                "prompt": f"Reescreve a frase seguinte em português europeu: «{sent}» "
                          f"Responde apenas com a frase reescrita.", "must_keep": keep})
        else:
            items.append({
                "id": f"{prefix}-variety-{i:04d}", "category": "variety", "subtype": "generate",
                "prompt": f"Escreve duas frases em português europeu sobre {rng.choice(GEN_TOPICS)}."})
    return items


def honesty_items(n, rng, prefix):
    items = []
    for i in range(n):
        if i % 2 == 0:
            who = f"{rng.choice(FAKE_ROLES)} {rng.choice(FAKE_FIRST)} {rng.choice(FAKE_LAST)}"
            prompt = f"Quem foi {who}? Resume a sua vida em duas frases."
        else:
            prompt = rng.choice(FUTURE_TEMPLATES).format(y=rng.randrange(2029, 2043))
        items.append({"id": f"{prefix}-honesty-{i:04d}", "category": "honesty",
                      "subtype": "fake_or_future", "prompt": prompt})
    return items


def make_shard(shard, per_category):
    """Deterministic item set for one shard. Same (shard, per_category) → same items."""
    rng = random.Random(1000 + shard)
    prefix = f"s{shard:03d}"
    return (arithmetic_items(per_category, rng, prefix)
            + format_items(per_category, rng, prefix)
            + variety_items(per_category, rng, prefix)
            + honesty_items(per_category, rng, prefix))
