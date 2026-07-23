"""
modifiability_scenarios.py — LLM calls for the modifiability-analysis
pipeline: generate future scenarios from a project's user stories, produce a
minimally-modified architecture for one scenario, and render that modified
architecture to PlantUML. All three are single litellm.completion() calls —
no openhands Agent/sandboxing, same reasoning as src/adr_agent.py.
"""
from __future__ import annotations

import json
import os
import re

import litellm

from src.prompt import KNOWLEDGE_BASE

SCENARIO_GENERATION_PROMPT = """
## Task
Read the following system description and user stories, then propose {n}
plausible FUTURE scenarios — new requirements not already covered — that
this system might need to support later.

## System Description and User Stories
{input_text}

## Output Format
Respond with ONLY a JSON array in a fenced code block, exactly {n} objects:

```json
[
  {{
    "description": "<one new requirement, phrased as a concrete capability>",
    "weight": <integer 1-5, how important/likely this scenario is>,
    "magnitude": "<small|medium|large, how big a change this would require>"
  }}
]
```

## Rules
- Each scenario must be a plausible extension of the existing system, not a
  rewrite of an existing user story.
- Vary the magnitude across the {n} scenarios — don't make them all the same size.
"""

ARCHITECTURE_EDIT_PROMPT = """
## Task
You are evolving an existing microservices architecture to support one new
scenario. Change or add ONLY what the scenario requires — leave every other
microservice, pattern, datastore, and dependency exactly as it is in the
existing architecture.

## Existing Architecture
{architecture_json}

## New Scenario
{scenario_description}

## Architectural Knowledge Base
Use the following pattern catalogue as reference when adding or modifying
patterns, following the same schema as the existing architecture:

{knowledge_base}

## Output Format
Respond with ONLY the full modified architecture as a JSON object in a
fenced code block, following the exact same schema as the Existing
Architecture above (microservices, patterns, datastores, dependencies).

## Constraints
- DO NOT remove or rename anything not directly affected by the scenario.
- DO NOT regenerate the whole architecture from scratch — start from the
  existing one and make the smallest change that satisfies the scenario.
"""

SCENARIO_RENDER_PROMPT = """
## Task
Generate a valid PlantUML component diagram for the following architecture,
following the same conventions used elsewhere in this project.

## Architecture
{architecture_json}

## Rules
- Every microservice -> a `[Component]` element with a readable quoted label.
- Every datastore -> a `database` element next to its owning service,
  connected with a plain `--` line (no label): `[service_alias] -- database_alias`.
- Every inter-service dependency -> a directed arrow labelled with the
  protocol (REST, WebSocket, event, gRPC).
- Microservices sharing the same architectural pattern -> grouped inside a
  `package` block named after the pattern.
- Use snake_case aliases; readable quoted strings as display labels.
- The file must start with `@startuml` and end with `@enduml`.

## Output Format
Respond with ONLY the PlantUML text (starting with `@startuml`, ending with
`@enduml`) — no commentary, no markdown code fences.
"""


def _extract_json(raw: str):
    """Parse a JSON object/array out of an LLM response, tolerating a
    ```json fenced code block around it."""
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
    json_str = m.group(1) if m else raw
    return json.loads(json_str)


def _complete(
    prompt: str,
    model: str | None = None,
    api_key: str | None = None,
    cost_tracker: list[float] | None = None,
) -> str:
    """cost_tracker: if given, the USD cost of this call (via
    litellm.completion_cost) is appended to it. Cost calculation can fail for
    unknown/local models — that's swallowed, not raised, since cost tracking
    must never break the actual LLM call.
    """
    model = model or os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    api_key = api_key or os.getenv("LLM_API_KEY")
    response = litellm.completion(
        model=model,
        api_key=api_key,
        messages=[{"role": "user", "content": prompt}],
    )
    if cost_tracker is not None:
        try:
            cost_tracker.append(litellm.completion_cost(completion_response=response))
        except Exception:
            pass
    return response.choices[0].message.content


def generate_scenarios(
    input_text: str,
    n: int = 5,
    model: str | None = None,
    api_key: str | None = None,
    cost_tracker: list[float] | None = None,
) -> list[dict]:
    prompt = SCENARIO_GENERATION_PROMPT.format(input_text=input_text, n=n)
    raw = _complete(prompt, model=model, api_key=api_key, cost_tracker=cost_tracker)
    return _extract_json(raw)


def modify_architecture(
    architecture: dict,
    scenario_description: str,
    model: str | None = None,
    api_key: str | None = None,
    cost_tracker: list[float] | None = None,
) -> dict:
    prompt = ARCHITECTURE_EDIT_PROMPT.format(
        architecture_json=json.dumps(architecture, indent=2),
        scenario_description=scenario_description,
        knowledge_base=KNOWLEDGE_BASE,
    )
    raw = _complete(prompt, model=model, api_key=api_key, cost_tracker=cost_tracker)
    return _extract_json(raw)


def render_scenario_diagram(
    architecture: dict,
    model: str | None = None,
    api_key: str | None = None,
    cost_tracker: list[float] | None = None,
) -> str:
    prompt = SCENARIO_RENDER_PROMPT.format(architecture_json=json.dumps(architecture, indent=2))
    return _complete(prompt, model=model, api_key=api_key, cost_tracker=cost_tracker)
