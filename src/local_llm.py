"""
local_llm.py — helpers for running diagram generation with local model inference.

Supported backends:
  ollama      — Ollama server (default http://localhost:11434)
               LiteLLM model string: "ollama/<model_name>"
  huggingface — HuggingFace TGI server (default http://localhost:8080)
  vllm       — vLLM's OpenAI-compatible server (default http://localhost:8000)
               LiteLLM model string: "openai/<model_name>"

Usage (env vars, highest priority wins):
  LOCAL_BACKEND   = ollama | huggingface | vllm
  LOCAL_MODEL     = <model name, e.g. qwen2.5-coder:32b or mistralai/Mistral-7B-Instruct-v0.3>
  LOCAL_BASE_URL  = override default server URL
"""

from __future__ import annotations

import os

_OLLAMA_DEFAULT_URL = "http://localhost:11434"
_HF_DEFAULT_URL = "http://localhost:8080"
_VLLM_DEFAULT_URL = "http://localhost:8000"


def _openai_base_url(url: str) -> str:
    """Normalize an OpenAI-compatible endpoint without duplicating ``/v1``."""
    clean = url.rstrip("/")
    return clean if clean.endswith("/v1") else f"{clean}/v1"


def get_local_llm_config(backend: str, model: str, base_url: str | None = None) -> dict:
    """
    Return a dict with 'model', 'api_key', 'base_url' suitable for
    passing to openhands.sdk.LLM(...).

    Args:
        backend:  'ollama', 'huggingface' (TGI), or 'vllm'
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

    if backend in ("huggingface", "hf", "tgi"):
        resolved_url = base_url or _HF_DEFAULT_URL
        return {
            "model": f"openai/{model}",
            "api_key": "local",           # placeholder; local servers commonly ignore it
            "base_url": _openai_base_url(resolved_url),
        }

    if backend == "vllm":
        resolved_url = base_url or _VLLM_DEFAULT_URL
        thinking_enabled = os.getenv("LOCAL_ENABLE_THINKING", "").lower() in ("1", "true", "yes")
        max_output_tokens = int(os.getenv("LOCAL_MAX_OUTPUT_TOKENS", "8192"))
        # Large local models can spend several minutes in prefill and hidden
        # reasoning before returning the first tool call. Keep this separate
        # from cloud-model defaults and make it tunable for a given server.
        request_timeout = int(os.getenv("LOCAL_LLM_TIMEOUT", "1200"))
        request_retries = int(os.getenv("LOCAL_LLM_RETRIES", "2"))
        # The vLLM frontend accepts graduated low/medium/high reasoning effort,
        # not just on/off. Allow overriding the "high" default so a run can
        # keep hidden reasoning without paying for the largest thinking budget.
        reasoning_effort = os.getenv("LOCAL_REASONING_EFFORT") or (
            "high" if thinking_enabled else "none"
        )
        # Each pipeline stage (extract/render/fix) is its own multi-turn agent
        # conversation, each iteration a full round-trip. On slower local
        # hardware this dominates wall-clock time far more than reasoning
        # effort does — let a run bound it explicitly instead of always
        # allowing the diagram_agent.py default of 30.
        max_agent_iterations = int(os.getenv("LOCAL_MAX_AGENT_ITERATIONS", "30"))
        # Some local models (observed: Gemma) narrate their reasoning as
        # ordinary visible prose instead of calling tools, even with
        # enable_thinking off, burning the whole output budget before ever
        # writing the target file. Opt-in per model via this flag rather
        # than changing the shared prompt for everyone.
        strict_tool_use = os.getenv("LOCAL_STRICT_TOOL_USE", "").lower() in ("1", "true", "yes")
        return {
            "model": f"openai/{model}" if not model.startswith("openai/") else model,
            "api_key": "local",
            "base_url": _openai_base_url(resolved_url),
            # Agent tasks need concise tool actions, not long hidden reasoning.
            "max_output_tokens": max_output_tokens,
            "timeout": request_timeout,
            "num_retries": request_retries,
            "reasoning_effort": reasoning_effort,
            "max_agent_iterations": max_agent_iterations,
            "strict_tool_use": strict_tool_use,
            "litellm_extra_body": {
                "chat_template_kwargs": {"enable_thinking": thinking_enabled},
            },
            # Keep local inference on the same OpenHands agent/tool framework
            # as cloud runs. Set LOCAL_DIRECT_GENERATION=1 only for a bounded
            # structured-completion smoke test.
            "direct_generation": os.getenv("LOCAL_DIRECT_GENERATION", "").lower() in ("1", "true", "yes"),
            "relaxed_output": os.getenv("LOCAL_RELAXED_OUTPUT", "").lower() in ("1", "true", "yes"),
        }

    raise ValueError(
        f"Unknown local backend '{backend}'. "
        "Supported values: 'ollama', 'huggingface' (aliases: 'hf', 'tgi'), 'vllm'"
    )


def describe_local_config(cfg: dict) -> str:
    return f"model={cfg['model']}  base_url={cfg['base_url']}"
