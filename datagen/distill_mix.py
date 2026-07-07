import os
import json
import tqdm
from mlx_lm import load, generate
import mlx.core as mx

def distil_file(model, tokenizer, input_path, output_path, limit=None):
    print(f"Distilling {input_path} -> {output_path} (limit: {limit})")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(input_path, "r", encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8") as f_out:
        lines = f_in.readlines()
        if limit:
            lines = lines[:limit]
        for line in tqdm.tqdm(lines):
            r = json.loads(line.strip())
            prompt = r["messages"][0]["content"]
            
            # Apply chat template
            templated_prompt = tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Generate response
            response = generate(model, tokenizer, prompt=templated_prompt, max_tokens=250, verbose=False)
            response = response.strip()
            
            # Save messages
            new_row = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response}
                ]
            }
            f_out.write(json.dumps(new_row, ensure_ascii=False) + "\n")
            f_out.flush()
            mx.clear_cache()

def main():
    try:
        mx.set_memory_limit(24 * 1024**3)
        mx.set_wired_limit(20 * 1024**3)
    except Exception:
        pass

    print("Loading AMALIA-9B MLX 8bit...")
    model, tokenizer = load("amalia-mlx-8bit")

    distil_file(model, tokenizer, "datagen/mix-v4/train.jsonl", "datagen/mix-v4-distilled/train.jsonl", limit=None)
    distil_file(model, tokenizer, "datagen/mix-v4/valid.jsonl", "datagen/mix-v4-distilled/valid.jsonl", limit=None)
    print("Distillation complete!")

if __name__ == "__main__":
    main()
