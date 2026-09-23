# Local Model Inference Setup (Qwen / Gemma on DGX Spark)

Working configuration as of 2026-09-22/23, arrived at after debugging slow
generation and Gemma tool-calling failures. Two separate NVIDIA DGX Spark
boxes, one model each, both served via a custom Rust vLLM frontend
(`VLLM_USE_RUST_FRONTEND=1`).

- Qwen box: `192.168.0.155:8000` — `unsloth/Qwen3.8-27B-NVFP4`
- Gemma box: `192.168.0.182:8000` — `unsloth/gemma-4-26B-A4B-it-NVFP4`

## vLLM server launch commands

### Qwen

```bash
docker run -d \
  --name vllm-server \
  --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  --entrypoint="" \
  -p 8000:8000 \
  -e HF_TOKEN="$HF_TOKEN" \
  -e VLLM_USE_RUST_FRONTEND=1 \
  -e VLLM_RUST_FRONTEND_PATH=auto \
  -v "$HOME/.cache/huggingface/hub:/root/.cache/huggingface/hub" \
  vllm/vllm-openai:latest \
  vllm serve "unsloth/Qwen3.8-27B-NVFP4" \
    --max-model-len 49152 \
    --gpu-memory-utilization 0.85 \
    --tensor-parallel-size 1 \
    --max-num-seqs 2 \
    --max-num-batched-tokens 12288 \
    --kv-cache-dtype fp8 \
    --enable-prefix-caching \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --reasoning-parser qwen3 \
    --default-chat-template-kwargs '{"enable_thinking":true}'
```

### Gemma

**Important:** `qwen3_coder` / `qwen3` parsers do NOT work on Gemma — it's a
different model family. The correct registered parser names (confirmed by
triggering the server's own "not registered, choose from: ..." error) are
`gemma4` for both tool-call and reasoning parsing. `--reasoning-parser` must
be set to match `--tool-call-parser` or the server rejects requests with
`"unified parsing requires the tool and reasoning selections to resolve to
the same parser"`.

```bash
docker run -d \
  --name vllm-server \
  --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  --entrypoint="" \
  -p 8000:8000 \
  -e HF_TOKEN="$HF_TOKEN" \
  -e VLLM_USE_RUST_FRONTEND=1 \
  -e VLLM_RUST_FRONTEND_PATH=auto \
  -v "$HOME/.cache/huggingface/hub:/root/.cache/huggingface/hub" \
  vllm/vllm-openai:latest \
  vllm serve "unsloth/gemma-4-26B-A4B-it-NVFP4" \
    --max-model-len 49152 \
    --gpu-memory-utilization 0.85 \
    --tensor-parallel-size 1 \
    --max-num-seqs 2 \
    --max-num-batched-tokens 12288 \
    --kv-cache-dtype fp8 \
    --enable-prefix-caching \
    --enable-auto-tool-choice \
    --tool-call-parser gemma4 \
    --reasoning-parser gemma4
```

### Why these flags, vs. the original launch command

| Flag | Original | Now | Why |
|---|---|---|---|
| `--max-model-len` | 131072 | 49152 | Actual prompts + `LOCAL_MAX_OUTPUT_TOKENS=32768` never need 128k; frees KV-cache room for concurrency |
| `--max-num-seqs` | 1 | 2 | Server was strictly serializing all requests (confirmed via `/metrics`: `num_requests_running` never exceeded 1). GPU KV-cache usage was ~0.5%, all headroom unused |
| `--kv-cache-dtype` | (unset) | fp8 | Halves KV-cache bytes read/written per step — matters more on Spark's bandwidth-bound unified memory than on a datacenter GPU |
| `--enable-prefix-caching` | (unset) | on | OpenHands' agent loop resends the same system prompt/tool schema every iteration. Confirmed working: Qwen showed ~67% cache hit rate after enabling |
| Gemma parsers | `qwen3_coder`/`qwen3` | `gemma4`/`gemma4` | Wrong model family's parser — caused hard 500 errors (`tokenizer is missing reasoning delimiter token <think>`, then `tool parsing is disabled`) until corrected |

**Untested beyond `--max-num-seqs 2`:** a throughput probe confirmed 2
concurrent requests complete in ~the same wall-clock time as 1 (aggregate
~89 tok/s vs ~47 tok/s single-stream on Gemma) — clean 2x scaling with
near-zero latency cost, consistent with Gemma's MoE architecture (~4B active
params of 26B total, per the `A4B` suffix) being cheap to batch. Worth
testing `--max-num-seqs 4` next, paired with `run_headless.py --workers 4`,
to actually capture this at the batch level — today's runs only ever used
`--workers 1`, so this throughput was never exploited.

## `run_headless.py` client-side configuration

All local-model env vars are read in `src/local_llm.py`. Current
recommendations per model, based on today's comparisons:

### Qwen — user preference: plain `none`-effort, no strict-tool-use

The `none` (thinking fully off) config finished successfully in ~12 min with
good-quality output; the `strict_tool_use` variant took longer (~18 min, due
to an extra syntax-fix pass) for output the user didn't prefer as much. Use:

```bash
LOCAL_ENABLE_THINKING=0 \
LOCAL_MAX_OUTPUT_TOKENS=32768 \
LOCAL_LLM_TIMEOUT=3600 \
LOCAL_LLM_RETRIES=2 \
python -u run_headless.py \
  --dataset dataset/student_projects \
  --output results/qwen38_27b/student_projects \
  --report results/reports/qwen38_27b_student_projects_report.csv \
  --force --workers 1 --local-backend vllm \
  --local-model unsloth/Qwen3.8-27B-NVFP4 \
  --local-url http://192.168.0.155:8000 \
  --progress-file dashboard/run_progress/qwen38-27b-student-projects.json \
  --dashboard-live
```

### Gemma — needs `LOCAL_STRICT_TOOL_USE=1` (still being validated)

Root cause (confirmed via token-usage telemetry, not guessed): with thinking
disabled, Gemma still "thinks" in plain visible text instead of the
suppressed reasoning channel, then tries to dump the entire `architecture.json`
as chat prose or as one giant `file_editor` argument (which breaks its own
tool-call serialization above ~4K tokens). `LOCAL_STRICT_TOOL_USE=1` adds an
extraction-stage instruction telling it to (a) act via tool calls, not prose,
and (b) build the file incrementally in small `file_editor` edits per
section rather than one large write. Iterating on this wording — see
`src/diagram_agent.py`'s `extract_extra_instructions` for the current text.

```bash
LOCAL_ENABLE_THINKING=0 \
LOCAL_STRICT_TOOL_USE=1 \
LOCAL_MAX_OUTPUT_TOKENS=32768 \
LOCAL_LLM_TIMEOUT=3600 \
LOCAL_LLM_RETRIES=2 \
python -u run_headless.py \
  --dataset dataset/student_projects \
  --output results/gemma4_26b_a4b/student_projects \
  --report results/reports/gemma4_26b_a4b_student_projects_report.csv \
  --force --workers 1 --local-backend vllm \
  --local-model unsloth/gemma-4-26B-A4B-it-NVFP4 \
  --local-url http://192.168.0.182:8000 \
  --progress-file dashboard/run_progress/gemma4-26b-a4b-student-projects.json \
  --dashboard-live
```

### Env var reference (`src/local_llm.py`)

| Var | Default | Purpose |
|---|---|---|
| `LOCAL_ENABLE_THINKING` | off | Sets `chat_template_kwargs.enable_thinking`. Confirmed: does NOT reliably stop verbose reasoning on Gemma — see `strict_tool_use` |
| `LOCAL_REASONING_EFFORT` | `high`/`none` based on thinking flag | Overrides to a specific `low`/`medium`/`high`/`none` value; server honors graduated effort (confirmed via `reasoning_tokens` in response `usage`) |
| `LOCAL_MAX_OUTPUT_TOKENS` | 8192 | Per-call cap; currently 32768 for both models |
| `LOCAL_MAX_AGENT_ITERATIONS` | 30 | Caps turns per pipeline stage (extract/render/fix each get their own `Conversation`, up to 3 retries each) |
| `LOCAL_STRICT_TOOL_USE` | off | Gemma-specific fix for the narrate/oversized-tool-call failure mode (see above) |
| `LOCAL_LLM_TIMEOUT` | 1200 | Per-request timeout, seconds |
| `LOCAL_LLM_RETRIES` | 2 | litellm-level retry count on transient errors |

## Known open items

- Gemma's prefix-cache hit rate was 0% in every run so far (vs. Qwen's
  ~67%) — not yet investigated why.
- `strict_tool_use` wording is on its third iteration; confirm the current
  version reaches `AGENT1: ✅` cleanly before trusting it for a full batch.
- `--max-num-seqs 4` (or higher) for Gemma is untested against a real OOM
  boundary — step up incrementally, not directly to a large value.
