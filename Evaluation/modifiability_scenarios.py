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
import time

import litellm

import src.deepseek_pricing  # noqa: F401 — side effect: registers deepseek-flash cost with litellm
from src.prompt import KNOWLEDGE_BASE

SCENARIO_GENERATION_PROMPT = """
## Task
Read the following system description and user stories, then propose {n}
plausible FUTURE scenarios — new requirements not already covered — that
this system might need to support later. Each scenario represents how the
specification would evolve over time: depending on its magnitude, it may
add one or more new user stories, and larger scenarios may also retire
existing user stories that this evolution would genuinely make obsolete.

## System Description and User Stories
{input_text}

## Output Format
Respond with ONLY a JSON array in a fenced code block, exactly {n} objects:

```json
[
  {{
    "description": "<short summary of the scenario, e.g. 'Add UAV-based aerial sampling'>",
    "weight": <integer 1-5, how important/likely this scenario is>,
    "magnitude": "<small|medium|large, how big a change this would require>",
    "new_user_stories": ["As a <role>, I want <capability>, so that <benefit>.", "..."],
    "removed_user_story_numbers": [<existing story number>, ...]
  }}
]
```

## Rules
- Each entry in "new_user_stories" MUST be phrased as a user story in the
  exact "As a <role>, I want <capability>, so that <benefit>." format used
  by the existing user stories above — not a general capability description.
- The NUMBER of new_user_stories and removed_user_story_numbers must scale
  with "magnitude":
  - small: exactly 1 new user story, no removals.
  - medium: 2-3 new user stories, 0-1 removals.
  - large: 3-5 new user stories, 1-3 removals.
- "removed_user_story_numbers" must reference real story numbers from the
  existing user stories above, and only when this scenario would genuinely
  make that story obsolete (e.g. replaced by a better approach) — never
  remove a story arbitrarily just to hit a quota. Use an empty array `[]`
  when nothing should be removed.
- Each scenario must be a plausible extension of the existing system, not a
  rewrite of an existing one.
- Vary the magnitude across the {n} scenarios — don't make them all the same size.
"""

ARCHITECTURE_EDIT_PROMPT = """
## Task
You are evolving an existing microservices architecture to support a
scenario's new user stories, and to remove support for any user stories
the scenario retires. Change or add ONLY what the new stories require, and
remove ONLY what the retired stories were driving — leave every other
microservice, pattern, datastore, and dependency exactly as it is in the
existing architecture.

## Existing Architecture
{architecture_json}

## Scenario
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
- DO NOT remove or rename anything not directly affected by the new or
  retired user stories above. If no stories are being retired, remove
  nothing.
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

SCENARIO_ADAPT_PROMPT = """
## Task
Adapt the following ORIGINAL PlantUML component diagram to reflect the
MODIFIED architecture below. This diagram is being compared against the
original to measure how much actually had to change, so it is critical that
you reuse the exact same aliases, groupings, and structure for every
component, datastore, and dependency that is unchanged between the original
and modified architecture. Only add, remove, or change what the modified
architecture actually requires.

## Original Diagram
{original_diagram}

## Modified Architecture
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

## Constraints
- DO NOT regenerate the diagram from scratch.
- DO NOT rename, reformat, reorder, or regroup anything that isn't directly
  affected by the modified architecture.
- Only touch what the modified architecture actually adds, removes, or changes.

## Output Format
Respond with ONLY the PlantUML text (starting with `@startuml`, ending with
`@enduml`) — no commentary, no markdown code fences.
"""


def _extract_json(raw: str):
    """Parse a JSON object/array out of an LLM response, tolerating a
    ```json fenced code block around it."""
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
    json_str = (m.group(1) if m else raw).strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        starts = [position for position in (json_str.find("{"), json_str.find("[")) if position >= 0]
        if not starts:
            raise
        value, _ = json.JSONDecoder().raw_decode(json_str[min(starts):])
        return value


def _json_is_complete(raw: str) -> bool:
    try:
        _extract_json(raw)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def _render_architecture(architecture: dict) -> str:
    """Deterministically render the shared architecture schema to PlantUML."""
    def alias(value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_]", "_", value).strip("_").lower() or "unnamed"

    services = architecture.get("microservices", architecture.get("services", []))
    patterns = architecture.get("patterns", [])
    datastores = architecture.get("datastores", [])
    service_aliases = {s.get("name", "unknown"): alias(s.get("name", "unknown")) for s in services}
    groups: dict[str, list[dict]] = {}
    for service in services:
        name = service.get("name", "unknown")
        matching_patterns = []
        for pattern in patterns:
            involved = pattern.get("involved_microservices", pattern.get("services", []))
            if name in involved:
                matching_patterns.append(pattern)
        primary = next(
            (
                pattern for pattern in matching_patterns
                if pattern.get("implementation_pattern", pattern.get("pattern", "")).strip().lower()
                != "database per service"
            ),
            matching_patterns[0] if matching_patterns else None,
        )
        group = (
            primary.get("group_name", primary.get("implementation_pattern", "uncategorized"))
            if primary else "uncategorized"
        )
        groups.setdefault(group, []).append(service)

    lines = ["@startuml", "skinparam componentStyle rectangle", ""]
    datastore_links = []
    for group, grouped_services in groups.items():
        lines.append(f'package "{group}" as pkg_{alias(group)} {{')
        for service in grouped_services:
            name = service.get("name", "unknown")
            service_alias = service_aliases[name]
            memberships = [
                str(pattern.get("implementation_pattern", pattern.get("pattern", "")))
                for pattern in patterns
                if name in pattern.get("involved_microservices", pattern.get("services", []))
            ]
            stereotype = f' <<{"; ".join(dict.fromkeys(memberships))}>>' if memberships else ""
            lines.append(f'  component "{name}" as {service_alias}{stereotype}')
            for datastore in datastores:
                owner = datastore.get("associated_microservice", datastore.get("owner", ""))
                if owner == name:
                    datastore_name = datastore.get("datastore_name", datastore.get("name", "db"))
                    datastore_alias = alias(datastore_name)
                    lines.append(f'  database "{datastore_name}" as {datastore_alias}')
                    datastore_links.append((service_alias, datastore_alias))
        lines.extend(["}", ""])
    lines.extend(f"{service} -- {datastore}" for service, datastore in datastore_links)
    for dependency in architecture.get("dependencies", []):
        source = service_aliases.get(dependency.get("from", ""), alias(dependency.get("from", "")))
        target = service_aliases.get(dependency.get("to", ""), alias(dependency.get("to", "")))
        lines.append(f"{source} --> {target} : {dependency.get('protocol', 'REST')}")
    lines.extend(["", "@enduml"])
    return "\n".join(lines) + "\n"


def _complete(
    prompt: str,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    cost_tracker: list[float] | None = None,
    timeout: float | None = None,
) -> str:
    """cost_tracker: if given, the USD cost of this call (via
    litellm.completion_cost) is appended to it. Cost calculation can fail for
    unknown/local models — that's swallowed, not raised, since cost tracking
    must never break the actual LLM call.

    timeout: request timeout in seconds, forwarded to litellm.completion().
    litellm/the underlying provider SDK apply NO timeout by default — a
    stalled connection hangs forever rather than raising, which a caller
    can't distinguish from "still legitimately working." Defaults to
    LLM_REQUEST_TIMEOUT (env, seconds) or 180.0.
    """
    model = model or os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    api_key = api_key or os.getenv("LLM_API_KEY")
    base_url = base_url or os.getenv("LLM_BASE_URL")
    timeout = timeout if timeout is not None else float(os.getenv("LLM_REQUEST_TIMEOUT", "180"))
    request_kwargs = dict(
        model=model,
        api_key=api_key,
        messages=[{"role": "user", "content": prompt}],
        timeout=timeout,
    )
    if base_url:
        request_kwargs["api_base"] = base_url.rstrip("/")
    max_output_tokens = os.getenv("LLM_MAX_OUTPUT_TOKENS")
    if max_output_tokens:
        request_kwargs["max_tokens"] = int(max_output_tokens)
    if os.getenv("LLM_DISABLE_THINKING", "").lower() in ("1", "true", "yes"):
        request_kwargs["extra_body"] = {
            "chat_template_kwargs": {"enable_thinking": False},
        }
    stream_early = os.getenv("LLM_STREAM_EARLY_STOP", "").lower() in ("1", "true", "yes")
    if stream_early:
        parts: list[str] = []
        response = litellm.completion(**request_kwargs, stream=True)
        last_update = time.monotonic()
        expects_puml = "@startuml" in prompt and "@enduml" in prompt
        try:
            for chunk in response:
                choices = getattr(chunk, "choices", None) or []
                delta = getattr(choices[0], "delta", None) if choices else None
                content = getattr(delta, "content", None) if delta is not None else None
                if content:
                    parts.append(content)
                combined = "".join(parts)
                now = time.monotonic()
                if now - last_update >= 15:
                    print(f"[modifiability] streamed {len(combined)} chars", flush=True)
                    last_update = now
                if (expects_puml and "@enduml" in combined.lower()) or (
                    not expects_puml and combined and _json_is_complete(combined)
                ):
                    break
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()
        return "".join(parts)

    response = litellm.completion(**request_kwargs)
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
    original_diagram: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    cost_tracker: list[float] | None = None,
) -> str:
    """Render the (already-edited) architecture to PlantUML.

    original_diagram: if given, the LLM is asked to ADAPT this diagram
        minimally rather than regenerate one from scratch — reusing the same
        aliases/grouping for anything unchanged. This matters because the
        rendered diagram is what graph edit distance is measured against;
        without an anchor, the LLM could re-render unchanged components
        differently each time (different aliases, grouping order), which
        would inflate GED with noise unrelated to the actual user story.
    """
    if os.getenv("LLM_DETERMINISTIC_RENDER", "").lower() in ("1", "true", "yes"):
        return _render_architecture(architecture)
    if original_diagram:
        prompt = SCENARIO_ADAPT_PROMPT.format(
            original_diagram=original_diagram,
            architecture_json=json.dumps(architecture, indent=2),
        )
    else:
        prompt = SCENARIO_RENDER_PROMPT.format(architecture_json=json.dumps(architecture, indent=2))
    return _complete(prompt, model=model, api_key=api_key, cost_tracker=cost_tracker)
