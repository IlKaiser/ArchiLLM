"""
local_llm.py — helpers for running diagram generation with local model inference.

Supported backends:
  ollama      — Ollama server (default http://localhost:11434)
               LiteLLM model string: "ollama/<model_name>"
  huggingface — HuggingFace TGI or vLLM server (default http://localhost:8080)
               LiteLLM model string: "huggingface/<model_name>"  (TGI)
               or "openai/<model_name>" pointed at a vLLM base_url

Usage (env vars, highest priority wins):
  LOCAL_BACKEND   = ollama | huggingface
  LOCAL_MODEL     = <model name, e.g. qwen2.5-coder:32b or mistralai/Mistral-7B-Instruct-v0.3>
  LOCAL_BASE_URL  = override default server URL
"""

from __future__ import annotations

_OLLAMA_DEFAULT_URL = "http://192.168.1.52:11434"
_HF_DEFAULT_URL = "http://localhost:8080"


def get_local_llm_config(backend: str, model: str, base_url: str | None = None) -> dict:
    """
    Return a dict with 'model', 'api_key', 'base_url' suitable for
    passing to openhands.sdk.LLM(...).

    Args:
        backend:  'ollama' or 'huggingface'
        model:    bare model name (e.g. 'qwen2.5-coder:32b' or
                  'mistralai/Mistral-7B-Instruct-v0.3')
        base_url: optional override; defaults to localhost port for each backend
    """
    backend = backend.lower().strip()

    if backend == "ollama":
        resolved_url = base_url or _OLLAMA_DEFAULT_URL
        # LiteLLM expects "ollama/model-name" + base_url pointing at Ollama
        litellm_model = f"ollama/{model}" if not model.startswith("ollama/") else model
        return {
            "model": litellm_model,
            "api_key": "ollama",          # LiteLLM requires a non-empty string
            "base_url": resolved_url,
        }

    if backend in ("huggingface", "hf", "tgi", "vllm"):
        resolved_url = base_url or _HF_DEFAULT_URL
        # TGI / vLLM both expose an OpenAI-compatible API — use the openai/ prefix
        # so LiteLLM routes through its OpenAI-compatible path
        litellm_model = f"openai/{model}" if "/" not in model.split(":")[-1] else f"openai/{model}"
        return {
            "model": litellm_model,
            "api_key": "local",           # placeholder; TGI/vLLM don't check the key
            "base_url": resolved_url + "/v1",
        }

    raise ValueError(
        f"Unknown local backend '{backend}'. "
        "Supported values: 'ollama', 'huggingface' (alias: 'hf', 'tgi', 'vllm')"
    )


def describe_local_config(cfg: dict) -> str:
    return f"model={cfg['model']}  base_url={cfg['base_url']}"
