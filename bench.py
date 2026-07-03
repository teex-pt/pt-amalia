"""Benchmark a model variant (BF16 / quantized) for the AMALIA comparison.

Usage: python bench.py --model <hf-repo-or-local-path> --label bf16
Writes bench-<label>.json (raw numbers) and bench-<label>.md (readable outputs).
Deterministic: greedy sampling (temp 0), fixed prompts, fixed perplexity text.
"""

import argparse
import json
import platform
import time

import mlx.core as mx
from mlx_lm import load, stream_generate

# Cap MLX so a runaway allocation errors out instead of wiring all RAM and
# freezing macOS (wired memory cannot be paged out).
try:
    mx.set_memory_limit(24 * 1024**3)
except Exception:
    pass
try:
    mx.set_wired_limit(20 * 1024**3)
except Exception:
    pass

PROMPTS = [
    {
        "id": "cultura",
        "max_tokens": 200,
        "text": "Quem foi Luís de Camões e qual a importância d'Os Lusíadas na literatura portuguesa? Responde em três frases.",
    },
    {
        "id": "gramatica-pt-pt",
        "max_tokens": 120,
        "text": "Reescreve a frase seguinte em português europeu formal: 'Vou estar a mandar o email pra você amanhã de manhã.' Responde apenas com a frase corrigida.",
    },
    {
        "id": "resumo",
        "max_tokens": 120,
        "text": "Resume o seguinte texto numa única frase: 'A rede de metro de Lisboa foi inaugurada em 1959, sendo a primeira do país. Atualmente conta com quatro linhas — Azul, Amarela, Verde e Vermelha — que servem a capital e alguns concelhos limítrofes. Nos últimos anos, a rede tem sido alvo de projetos de expansão, incluindo a linha circular e o prolongamento até Alcântara, com o objetivo de reduzir o tráfego automóvel e as emissões na cidade.'",
    },
    {
        "id": "raciocinio",
        "max_tokens": 250,
        "text": "Um comboio parte de Lisboa às 9h15 e demora 2 horas e 50 minutos a chegar ao Porto. A que horas chega? Explica o raciocínio passo a passo.",
    },
    {
        "id": "traducao",
        "max_tokens": 120,
        "text": "Traduz para português de Portugal: 'The meeting has been rescheduled to next Wednesday at 3 p.m. Please let me know if that works for you.' Responde apenas com a tradução.",
    },
    {
        "id": "json",
        "max_tokens": 250,
        "text": 'Lista exatamente 5 pratos tradicionais portugueses em formato JSON: um array de objetos com os campos "nome" e "regiao". Responde apenas com o JSON.',
    },
]

PPL_TEXT = (
    "Portugal é um país situado no sudoeste da Europa, cujo território se localiza na zona "
    "ocidental da Península Ibérica e em arquipélagos no Atlântico Norte. A língua portuguesa, "
    "falada por mais de duzentos e cinquenta milhões de pessoas em todo o mundo, é uma das "
    "línguas mais faladas do planeta e constitui um dos pilares fundamentais da identidade "
    "nacional. A literatura portuguesa, desde as cantigas medievais até aos romances "
    "contemporâneos, reflete a história de um povo marcado pelas descobertas marítimas, pela "
    "saudade e por uma relação profunda com o mar. Fernando Pessoa escreveu que a sua pátria "
    "era a língua portuguesa, sublinhando a importância do idioma como território simbólico "
    "que ultrapassa fronteiras geográficas. Nas últimas décadas, Portugal tem apostado na "
    "ciência, na tecnologia e na inovação, procurando afirmar-se como um centro europeu de "
    "investigação e empreendedorismo, sem perder de vista o património cultural que o "
    "distingue: o fado, a azulejaria, a gastronomia e as tradições populares que atravessam "
    "gerações e continuam vivas nas cidades e aldeias de todo o país."
)

NEEDLE_SENTENCE = "A palavra-chave secreta desta tarefa é 'azulejo'."
NEEDLE_QUESTION = "Com base no texto acima, qual é a palavra-chave secreta? Responde apenas com a palavra."


def bench_prompt(model, tokenizer, content, max_tokens):
    messages = [{"role": "user", "content": content}]
    ids = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
    text = ""
    last = None
    t0 = time.time()
    for r in stream_generate(model, tokenizer, ids, max_tokens=max_tokens):
        text += r.text
        last = r
    return {
        "output": text.strip(),
        "prompt_tokens": last.prompt_tokens,
        "prompt_tps": round(last.prompt_tps, 1),
        "gen_tokens": last.generation_tokens,
        "gen_tps": round(last.generation_tps, 1),
        "peak_mem_gb": round(last.peak_memory, 2),
        "wall_s": round(time.time() - t0, 1),
    }


def perplexity(model, tokenizer, text):
    tokens = tokenizer.encode(text)
    inputs = mx.array([tokens[:-1]])
    targets = mx.array([tokens[1:]])
    logits = model(inputs).astype(mx.float32)
    logprobs = logits - mx.logsumexp(logits, axis=-1, keepdims=True)
    nll = -mx.take_along_axis(logprobs, targets[..., None], axis=-1).squeeze(-1)
    return {"tokens": len(tokens), "ppl": round(float(mx.exp(nll.mean())), 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    args = ap.parse_args()

    results = {
        "label": args.label,
        "model": args.model,
        "machine": platform.machine(),
        "mlx_version": mx.__version__,
    }

    t0 = time.time()
    model, tokenizer = load(args.model)
    results["load_time_s"] = round(time.time() - t0, 1)
    print(f"model loaded in {results['load_time_s']}s", flush=True)

    # warmup so compile time doesn't pollute the first measurement
    t0 = time.time()
    ids = tokenizer.apply_chat_template(
        [{"role": "user", "content": "Olá"}], add_generation_prompt=True
    )
    for _ in stream_generate(model, tokenizer, ids, max_tokens=5):
        pass
    results["warmup_s"] = round(time.time() - t0, 1)
    print(f"warmup done in {results['warmup_s']}s", flush=True)

    results["prompts"] = {}
    for p in PROMPTS:
        results["prompts"][p["id"]] = bench_prompt(model, tokenizer, p["text"], p["max_tokens"])
        mx.clear_cache()
        print(f"done: {p['id']}", flush=True)

    # long context: paragraph repeated with a needle in the middle
    blocks = [PPL_TEXT] * 8
    blocks.insert(4, NEEDLE_SENTENCE)
    long_prompt = "\n\n".join(blocks) + "\n\n" + NEEDLE_QUESTION
    results["long_context"] = bench_prompt(model, tokenizer, long_prompt, 30)
    results["long_context"]["needle_found"] = "azulejo" in results["long_context"]["output"].lower()
    print("done: long_context", flush=True)

    results["perplexity"] = perplexity(model, tokenizer, PPL_TEXT)
    results["overall_peak_mem_gb"] = round(mx.get_peak_memory() / 1e9, 2)
    print("done: perplexity", flush=True)

    with open(f"bench-{args.label}.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    md = [f"# AMALIA-9B — {args.label}\n"]
    md.append(f"- model: `{args.model}`")
    md.append(f"- load: {results['load_time_s']}s | warmup: {results['warmup_s']}s")
    md.append(f"- perplexity (fixed pt-PT text): **{results['perplexity']['ppl']}**")
    md.append(f"- overall peak memory: **{results['overall_peak_mem_gb']} GB**\n")
    for p in PROMPTS:
        r = results["prompts"][p["id"]]
        md.append(f"## {p['id']}  ({r['gen_tps']} tok/s gen, {r['prompt_tps']} tok/s prompt, {r['gen_tokens']} tokens)")
        md.append(f"> {p['text']}\n")
        md.append(r["output"] + "\n")
    lc = results["long_context"]
    md.append(f"## long-context needle  ({lc['prompt_tokens']} prompt tokens, {lc['prompt_tps']} tok/s prompt, needle_found={lc['needle_found']})")
    md.append(lc["output"] + "\n")
    with open(f"bench-{args.label}.md", "w") as f:
        f.write("\n".join(md))

    print(json.dumps({k: v for k, v in results.items() if k != "prompts"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
