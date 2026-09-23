"""Registers DeepSeek V4.1 Flash pricing with litellm.

litellm's pinned version (1.81.14) predates DeepSeek V4.1 Flash (released
2026-09-10), so it has no pricing entry for it: any cost computed via
litellm (conversation_stats.accumulated_cost, litellm.completion_cost, …)
silently comes back as $0 for every deepseek-flash call, which means a
--max-cost budget guard never trips even as real money is spent.

Register peak-rate pricing (the conservative choice — it won't under-count
spend) ourselves, but only if litellm doesn't already have an entry, so a
future litellm upgrade with real pricing wins instead.

Import this (for its side effect) in every module that makes deepseek-flash
calls through litellm — src/diagram_agent.py and
Evaluation/modifiability_scenarios.py both need it; they don't share an
import path that would otherwise cover both.
"""
import litellm

_DEEPSEEK_FLASH_COST = {
    "input_cost_per_token": 0.30 / 1_000_000,              # peak, cache miss
    "input_cost_per_token_cache_hit": 0.006 / 1_000_000,   # peak, cache hit
    "cache_read_input_token_cost": 0.006 / 1_000_000,
    "cache_creation_input_token_cost": 0.0,
    "output_cost_per_token": 1.20 / 1_000_000,             # peak
    "litellm_provider": "deepseek",
    "mode": "chat",
    "max_input_tokens": 1_000_000,
    "max_output_tokens": 8192,
    "max_tokens": 8192,
    "supports_prompt_caching": True,
    "source": "https://api-docs.deepseek.com/quick_start/pricing (V4.1 Flash peak rate, 2026-09-10)",
}
for _model_key in ("deepseek/deepseek-flash", "deepseek-flash"):
    if _model_key not in litellm.model_cost:
        litellm.register_model({_model_key: _DEEPSEEK_FLASH_COST})
