#!/bin/zsh
set -e
cd /Users/filipemartins/Development/teex/pt-amalia

echo "=== [1/6] installing llama.cpp (brew) ==="
brew list llama.cpp >/dev/null 2>&1 || brew install llama.cpp

echo "=== [2/6] cloning llama.cpp repo (converter script) ==="
[ -d llama.cpp ] || git clone --depth 1 https://github.com/ggml-org/llama.cpp

echo "=== [3/6] installing converter python deps ==="
./.venv/bin/pip install --quiet -r llama.cpp/requirements/requirements-convert_hf_to_gguf.txt

echo "=== [4/6] converting HF safetensors -> BF16 GGUF ==="
SNAP=$(find ~/.cache/huggingface/hub/models--amalia-llm--AMALIA-9B-0626-DPO/snapshots -maxdepth 1 -type d | tail -1)
mkdir -p gguf
[ -f gguf/AMALIA-9B-0626-DPO-BF16.gguf ] || ./.venv/bin/python llama.cpp/convert_hf_to_gguf.py "$SNAP" \
  --outfile gguf/AMALIA-9B-0626-DPO-BF16.gguf --outtype bf16

echo "=== [5/6] quantizing Q4_K_M and Q8_0 ==="
[ -f gguf/AMALIA-9B-0626-DPO-Q4_K_M.gguf ] || llama-quantize gguf/AMALIA-9B-0626-DPO-BF16.gguf gguf/AMALIA-9B-0626-DPO-Q4_K_M.gguf Q4_K_M
[ -f gguf/AMALIA-9B-0626-DPO-Q8_0.gguf ] || llama-quantize gguf/AMALIA-9B-0626-DPO-BF16.gguf gguf/AMALIA-9B-0626-DPO-Q8_0.gguf Q8_0

echo "=== [6/6] smoke tests + perplexity ==="
for q in Q4_K_M Q8_0; do
  echo "--- smoke $q:"
  llama-cli -m "gguf/AMALIA-9B-0626-DPO-$q.gguf" -p "Explica numa frase o que é o fado." -n 48 --temp 0 -no-cnv --no-display-prompt 2>/dev/null | tail -3
done
for q in Q4_K_M Q8_0; do
  echo "--- perplexity $q (same pt-PT text as MLX bench, llama.cpp scale):"
  llama-perplexity -m "gguf/AMALIA-9B-0626-DPO-$q.gguf" -f ppl-pt.txt -c 512 2>&1 | grep -iE "final estimate|ppl" | tail -2
done
ls -lh gguf/
echo "GGUF PIPELINE DONE"
