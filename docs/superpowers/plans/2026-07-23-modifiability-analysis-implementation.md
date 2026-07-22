# Modifiability Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Modifiability Analysis" evaluation dimension: generate LLM-authored future scenarios from a project's user stories, produce a minimally-modified architecture per scenario, and measure the real graph edit distance (networkx) between the original and modified component diagrams, weighted by scenario importance, into one Modifiability Score (lower = more flexible).

**Architecture:** Three focused `Evaluation/` modules (scenario/edit/render LLM calls; graph building + GED; orchestrator) plus one Streamlit section appended to `app.py`, following the exact conventions established by the ADR pipeline (`src/adr_agent.py`, `Evaluation/adr_judge.py`, `src/adr_frontend.py`): lightweight single-shot `litellm.completion()` calls, no openhands Agent/sandboxing, per-scenario try/except so one failure doesn't abort the batch, and additive-only `app.py` changes.

**Tech Stack:** `litellm`, `networkx==3.4.2` (new pin), `scipy` (networkx's `graph_edit_distance` dependency), `streamlit`, `pytest`. Reuses the existing `Evaluation/uml_parser.py` (`UMLParser`) and `src/prompt.py` (`KNOWLEDGE_BASE`) — no new parsing code, per the user's explicit instruction to reuse the existing diagram-to-graph conversion.

## Global Constraints

- Operates only on a project that has already been run through the main diagram pipeline: `run/{project}/architecture.json` and `run/{project}/component_diagram.puml` must exist. Missing either raises `FileNotFoundError` with a message telling the user to run the diagram pipeline first — no fallback generation.
- Graph construction reuses `Evaluation.uml_parser.UMLParser` exactly as-is (already used by `Evaluation/metrics_calculator.py`) — do not write a new PlantUML parser.
- Do **not** import anything from `src.diagram_agent` anywhere in this feature. That module imports the full `openhands` SDK at module level, which is not installed in this environment; importing it eagerly from a lightweight module would break `app.py` startup for anyone without the full openhands stack. `UMLParser.parse()` already degrades gracefully on malformed PlantUML (returns empty nodes/edges rather than raising) — that, combined with per-scenario try/except, is the only safety net needed.
- `nx.graph_edit_distance(...)` is the real (exact, bounded-by-timeout) networkx algorithm — no custom approximation or metaheuristic layer of our own. Must be called with an explicit `node_match` comparing a `"label"` node attribute, otherwise networkx treats all nodes as freely substitutable and GED would undercount real structural differences.
- One scenario's LLM call failing, or producing an unparseable diagram, must not abort the whole batch: wrap the per-scenario work in try/except, record `{"error": str(e), "ged": None, "exact": False, "weighted_ged": None}` for that scenario, and continue — same pattern as `Evaluation/adr_judge.py`'s per-ADR failure handling. If `graph_edit_distance` returns `None` (timeout with no candidate found), record the same `ged: None` shape (no `"error"` key needed in that case — it's an inconclusive result, not a failure).
- `modifiability_score` = sum of `weighted_ged` over scenarios with non-null `ged` only. **Lower is better.**
- `app.py`'s existing content must not be modified — only new sidebar-free, additive changes: one appended `render_modifiability_section(project_name=proj_name)` call at the very end of the file (`proj_name` is already in scope from the existing dataset-project dropdown).
- Environment note: `networkx.graph_edit_distance` depends on `scipy.optimize.linear_sum_assignment`. The development/test venv for this plan must be a **clean pip venv**, not the machine's base conda environment (its `scipy` install is broken — unrelated pre-existing issue, verified separately). `pip install networkx==3.4.2 scipy` in a fresh venv works correctly.

---

### Task 1: `Evaluation/modifiability_scenarios.py` — LLM calls

**Files:**
- Create: `Evaluation/modifiability_scenarios.py`
- Test: `tests/test_modifiability_scenarios.py`

**Interfaces:**
- Consumes: `src.prompt.KNOWLEDGE_BASE` (existing constant, read-only).
- Produces:
  - `generate_scenarios(input_text: str, n: int = 5, model: str | None = None, api_key: str | None = None) -> list[dict]` — each dict has keys `"description"`, `"weight"`, `"magnitude"`. Consumed by Task 3.
  - `modify_architecture(architecture: dict, scenario_description: str, model: str | None = None, api_key: str | None = None) -> dict` — returns a full architecture dict. Consumed by Task 3.
  - `render_scenario_diagram(architecture: dict, model: str | None = None, api_key: str | None = None) -> str` — returns raw PlantUML text. Consumed by Task 3.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_modifiability_scenarios.py`:

```python
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Evaluation import modifiability_scenarios as ms


def test_extract_json_parses_fenced_array():
    raw = '```json\n[{"a": 1}]\n```'
    assert ms._extract_json(raw) == [{"a": 1}]


def test_extract_json_parses_bare_object_without_fence():
    raw = '{"a": 1}'
    assert ms._extract_json(raw) == {"a": 1}


def test_generate_scenarios_calls_litellm_and_parses_json(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = (
        '```json\n'
        '[{"description": "Add SMS notifications", "weight": 3, "magnitude": "small"},'
        ' {"description": "Support multi-region deployment", "weight": 5, "magnitude": "large"}]'
        '\n```'
    )
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)

    scenarios = ms.generate_scenarios("some input text", n=2, model="test/model", api_key="test-key")

    assert len(scenarios) == 2
    assert scenarios[0]["description"] == "Add SMS notifications"
    assert scenarios[1]["magnitude"] == "large"
    call_kwargs = fake_completion.call_args.kwargs
    assert call_kwargs["model"] == "test/model"
    assert call_kwargs["api_key"] == "test-key"
    assert "some input text" in call_kwargs["messages"][0]["content"]
    assert "2" in call_kwargs["messages"][0]["content"]


def test_modify_architecture_embeds_existing_architecture_and_scenario(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = '```json\n{"microservices": [], "patterns": []}\n```'
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)

    architecture = {"microservices": [{"name": "order_service"}], "patterns": []}
    result = ms.modify_architecture(architecture, "Add SMS notifications", model="test/model", api_key="test-key")

    assert result == {"microservices": [], "patterns": []}
    call_kwargs = fake_completion.call_args.kwargs
    prompt_text = call_kwargs["messages"][0]["content"]
    assert "order_service" in prompt_text
    assert "Add SMS notifications" in prompt_text


def test_render_scenario_diagram_returns_plain_puml_text(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "@startuml\n[order_service]\n@enduml"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)

    result = ms.render_scenario_diagram({"microservices": []}, model="test/model", api_key="test-key")

    assert result == "@startuml\n[order_service]\n@enduml"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_modifiability_scenarios.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'Evaluation.modifiability_scenarios'`.

- [ ] **Step 3: Implement `Evaluation/modifiability_scenarios.py`**

```python
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


def _complete(prompt: str, model: str | None = None, api_key: str | None = None) -> str:
    model = model or os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    api_key = api_key or os.getenv("LLM_API_KEY")
    response = litellm.completion(
        model=model,
        api_key=api_key,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def generate_scenarios(
    input_text: str, n: int = 5, model: str | None = None, api_key: str | None = None
) -> list[dict]:
    prompt = SCENARIO_GENERATION_PROMPT.format(input_text=input_text, n=n)
    raw = _complete(prompt, model=model, api_key=api_key)
    return _extract_json(raw)


def modify_architecture(
    architecture: dict, scenario_description: str, model: str | None = None, api_key: str | None = None
) -> dict:
    prompt = ARCHITECTURE_EDIT_PROMPT.format(
        architecture_json=json.dumps(architecture, indent=2),
        scenario_description=scenario_description,
        knowledge_base=KNOWLEDGE_BASE,
    )
    raw = _complete(prompt, model=model, api_key=api_key)
    return _extract_json(raw)


def render_scenario_diagram(
    architecture: dict, model: str | None = None, api_key: str | None = None
) -> str:
    prompt = SCENARIO_RENDER_PROMPT.format(architecture_json=json.dumps(architecture, indent=2))
    return _complete(prompt, model=model, api_key=api_key)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_modifiability_scenarios.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add Evaluation/modifiability_scenarios.py tests/test_modifiability_scenarios.py
git commit -m "feat: add LLM calls for modifiability scenario generation and architecture editing"
```

---

### Task 2: `Evaluation/modifiability_graph.py` — graph building + GED

**Files:**
- Create: `Evaluation/modifiability_graph.py`
- Modify: `environment.yml` (add `networkx==3.4.2` pin — not currently committed; the user has this line uncommitted locally for unrelated reasons, but a fresh checkout of this branch does not have it)
- Test: `tests/test_modifiability_graph.py`

**Interfaces:**
- Consumes: `Evaluation.uml_parser.UMLParser().parse(puml_text)` output shape (`{"nodes": [...], "edges": [(src, dst), ...], ...}` — existing, unchanged).
- Produces:
  - `build_graph(parsed: dict) -> networkx.DiGraph` — each node carries a `"label"` attribute equal to its name. Consumed by Task 3.
  - `compute_ged(g1: networkx.DiGraph, g2: networkx.DiGraph, timeout: float = 10.0) -> float | None`. Consumed by Task 3.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_modifiability_graph.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Evaluation import modifiability_graph as mg


def test_build_graph_creates_nodes_and_edges():
    parsed = {"nodes": ["Global::a", "Global::b"], "edges": [("Global::a", "Global::b")]}
    graph = mg.build_graph(parsed)

    assert set(graph.nodes) == {"Global::a", "Global::b"}
    assert graph.nodes["Global::a"]["label"] == "Global::a"
    assert list(graph.edges) == [("Global::a", "Global::b")]


def test_compute_ged_zero_for_identical_graphs():
    parsed = {"nodes": ["Global::a", "Global::b"], "edges": [("Global::a", "Global::b")]}
    g1 = mg.build_graph(parsed)
    g2 = mg.build_graph(parsed)

    assert mg.compute_ged(g1, g2, timeout=5.0) == 0


def test_compute_ged_positive_for_extra_node():
    parsed1 = {"nodes": ["Global::a", "Global::b"], "edges": [("Global::a", "Global::b")]}
    parsed2 = {"nodes": ["Global::a", "Global::b", "Global::c"], "edges": [("Global::a", "Global::b")]}
    g1 = mg.build_graph(parsed1)
    g2 = mg.build_graph(parsed2)

    ged = mg.compute_ged(g1, g2, timeout=5.0)

    assert ged is not None
    assert ged > 0


def test_compute_ged_respects_node_identity_not_just_count():
    # Same number of nodes/edges, but different names -> nodes must not be
    # freely substitutable, or this would incorrectly return 0.
    parsed1 = {"nodes": ["Global::a", "Global::b"], "edges": [("Global::a", "Global::b")]}
    parsed2 = {"nodes": ["Global::x", "Global::y"], "edges": [("Global::x", "Global::y")]}
    g1 = mg.build_graph(parsed1)
    g2 = mg.build_graph(parsed2)

    ged = mg.compute_ged(g1, g2, timeout=5.0)

    assert ged is not None
    assert ged > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_modifiability_graph.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'Evaluation.modifiability_graph'`.

- [ ] **Step 3: Implement `Evaluation/modifiability_graph.py`**

```python
"""
modifiability_graph.py — build networkx graphs from parsed PlantUML
diagrams (via Evaluation.uml_parser.UMLParser) and compute the real graph
edit distance between two architecture versions.
"""
from __future__ import annotations

import networkx as nx


def build_graph(parsed: dict) -> nx.DiGraph:
    """Build a directed graph from a UMLParser.parse() result
    ({"nodes": [...], "edges": [(src, dst), ...], ...}).
    Each node carries a "label" attribute equal to its name, so node_match
    in compute_ged can compare nodes by identity rather than treating all
    nodes as freely substitutable.
    """
    graph = nx.DiGraph()
    for node in parsed["nodes"]:
        graph.add_node(node, label=node)
    for src, dst in parsed["edges"]:
        graph.add_edge(src, dst)
    return graph


def compute_ged(g1: nx.DiGraph, g2: nx.DiGraph, timeout: float = 10.0) -> float | None:
    """Real (exact) graph edit distance via networkx, bounded by timeout.
    Returns None if no result was found within the timeout — callers should
    treat this as inconclusive, not as a zero distance.
    """
    return nx.graph_edit_distance(
        g1, g2,
        node_match=lambda a, b: a.get("label") == b.get("label"),
        timeout=timeout,
    )
```

- [ ] **Step 4: Pin `networkx` in `environment.yml`**

Read `environment.yml` first. If it does not already contain a `networkx==`
line (check with `grep networkx environment.yml` — it may already be present
as an uncommitted local change unrelated to this task; only add it if it's
missing from what `git show HEAD:environment.yml` contains), add this line
to the pip dependency list, alphabetically next to `narwhals==2.18.0`:

```
      - networkx==3.4.2
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_modifiability_graph.py -v`
Expected: PASS (4 tests). If this fails with an error mentioning
`libgfortran` or a `scipy` import error, you are running in an environment
with a broken `scipy` install (a known pre-existing issue unrelated to this
code) — use a clean pip venv instead (`python -m venv .venv && source
.venv/bin/activate && pip install networkx==3.4.2 scipy pytest litellm
openai streamlit python-dotenv pypdf openpyxl`).

- [ ] **Step 6: Commit**

```bash
git add Evaluation/modifiability_graph.py tests/test_modifiability_graph.py environment.yml
git commit -m "feat: add networkx graph building and graph edit distance for modifiability analysis"
```

---

### Task 3: `Evaluation/modifiability.py` — orchestrator

**Files:**
- Create: `Evaluation/modifiability.py`
- Test: `tests/test_modifiability.py`

**Interfaces:**
- Consumes: `Evaluation.modifiability_scenarios.{generate_scenarios, modify_architecture, render_scenario_diagram}` (Task 1), `Evaluation.modifiability_graph.{build_graph, compute_ged}` (Task 2), `Evaluation.uml_parser.UMLParser` (existing).
- Produces: `run(project_name: str, n_scenarios: int = 5, timeout: float = 10.0, run_dir: str = "run", dataset_dir: str = "dataset/student_projects") -> dict`. Returns and writes to `{run_dir}/{project_name}/modifiability/report.json` a dict with keys `"project"`, `"n_scenarios"`, `"scenarios"` (list of scenario dicts each with `"description"`, `"weight"`, `"magnitude"`, `"ged"`, `"exact"`, `"weighted_ged"`, optionally `"error"`), `"modifiability_score"`, `"by_magnitude"`. Consumed by Task 4.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_modifiability.py`:

```python
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Evaluation import modifiability


def _write_project(tmp_path, project_name="demo"):
    run_dir = tmp_path / "run" / project_name
    run_dir.mkdir(parents=True)
    architecture = {"microservices": [{"name": "order_service"}], "patterns": [], "datastores": [], "dependencies": []}
    (run_dir / "architecture.json").write_text(json.dumps(architecture), encoding="utf-8")
    (run_dir / "component_diagram.puml").write_text(
        "@startuml\n[order_service]\n@enduml", encoding="utf-8"
    )

    dataset_dir = tmp_path / "dataset" / project_name
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "input.txt").write_text(
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n# USER STORIES:\n1. As a user, I want to place orders.",
        encoding="utf-8",
    )
    return architecture


def test_load_original_raises_when_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        modifiability._load_original(str(tmp_path / "run"), "does-not-exist")


def test_run_raises_file_not_found_when_project_not_yet_generated(tmp_path):
    with pytest.raises(FileNotFoundError):
        modifiability.run(
            "does-not-exist",
            run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
        )


def test_run_scores_scenarios_and_writes_report(tmp_path, monkeypatch):
    _write_project(tmp_path)

    fake_scenarios = [
        {"description": "Add SMS notifications", "weight": 3, "magnitude": "small"},
        {"description": "Support multi-region deployment", "weight": 5, "magnitude": "large"},
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch: "@startuml\n[order_service]\n[new_service]\n@enduml",
    )

    report = modifiability.run(
        "demo", n_scenarios=2,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    assert report["project"] == "demo"
    assert report["n_scenarios"] == 2
    assert len(report["scenarios"]) == 2
    for scenario in report["scenarios"]:
        assert scenario["ged"] is not None
        assert scenario["exact"] is True
        assert scenario["weighted_ged"] == scenario["weight"] * scenario["ged"]
    assert report["modifiability_score"] == round(sum(s["weighted_ged"] for s in report["scenarios"]), 2)
    assert "small" in report["by_magnitude"]
    assert "large" in report["by_magnitude"]

    report_path = tmp_path / "run" / "demo" / "modifiability" / "report.json"
    assert report_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8")) == report


def test_run_continues_after_one_scenario_failure(tmp_path, monkeypatch):
    _write_project(tmp_path)

    fake_scenarios = [
        {"description": "Will fail", "weight": 2, "magnitude": "small"},
        {"description": "Will succeed", "weight": 4, "magnitude": "medium"},
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n: fake_scenarios)

    def flaky_modify(architecture, description):
        if description == "Will fail":
            raise ValueError("LLM exploded")
        return {"microservices": [{"name": "order_service"}, {"name": "extra"}]}

    monkeypatch.setattr(modifiability, "modify_architecture", flaky_modify)
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch: "@startuml\n[order_service]\n[extra]\n@enduml",
    )

    report = modifiability.run(
        "demo", n_scenarios=2,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    failed, succeeded = report["scenarios"]
    assert failed["ged"] is None
    assert failed["exact"] is False
    assert "error" in failed
    assert succeeded["ged"] is not None
    assert succeeded["weighted_ged"] == succeeded["weight"] * succeeded["ged"]
    # aggregate must only include the successful scenario
    assert report["modifiability_score"] == round(succeeded["weighted_ged"], 2)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_modifiability.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'Evaluation.modifiability'`.

- [ ] **Step 3: Implement `Evaluation/modifiability.py`**

```python
"""
modifiability.py — orchestrates the modifiability-analysis pipeline for one
project: generate future scenarios, modify the architecture for each,
measure graph edit distance against the baseline diagram, and aggregate into
a weighted Modifiability Score (lower is better).
"""
from __future__ import annotations

import json
from pathlib import Path

from Evaluation.modifiability_graph import build_graph, compute_ged
from Evaluation.modifiability_scenarios import (
    generate_scenarios,
    modify_architecture,
    render_scenario_diagram,
)
from Evaluation.uml_parser import UMLParser


def _load_original(run_dir: str, project_name: str) -> tuple[dict, dict]:
    """Read architecture.json + parse component_diagram.puml for
    project_name. Raises FileNotFoundError (with a clear message) if either
    is missing.
    """
    project_dir = Path(run_dir) / project_name
    arch_path = project_dir / "architecture.json"
    puml_path = project_dir / "component_diagram.puml"
    if not arch_path.exists() or not puml_path.exists():
        raise FileNotFoundError(
            f"Missing {arch_path} or {puml_path} — run the diagram pipeline "
            f"for '{project_name}' before running modifiability analysis."
        )
    architecture = json.loads(arch_path.read_text(encoding="utf-8"))
    parsed_original = UMLParser().parse(puml_path.read_text(encoding="utf-8"))
    return architecture, parsed_original


def _score_one_scenario(scenario: dict, architecture: dict, g_original, timeout: float) -> dict:
    """Run the edit -> render -> parse -> GED steps for one scenario. Never
    raises — records an "error" key in the returned dict on any failure
    instead, so one bad scenario doesn't abort the whole batch.
    """
    try:
        modified_arch = modify_architecture(architecture, scenario["description"])
        rendered = render_scenario_diagram(modified_arch)
        parsed_modified = UMLParser().parse(rendered)
        g_modified = build_graph(parsed_modified)
        ged = compute_ged(g_original, g_modified, timeout=timeout)
    except Exception as e:
        print(f"[modifiability] scenario failed: {scenario.get('description', '')[:60]!r} — {e}")
        return {**scenario, "error": str(e), "ged": None, "exact": False, "weighted_ged": None}

    if ged is None:
        print(f"[modifiability] GED inconclusive (timeout) for: {scenario.get('description', '')[:60]!r}")
        return {**scenario, "ged": None, "exact": False, "weighted_ged": None}

    return {**scenario, "ged": ged, "exact": True, "weighted_ged": scenario["weight"] * ged}


def run(
    project_name: str,
    n_scenarios: int = 5,
    timeout: float = 10.0,
    run_dir: str = "run",
    dataset_dir: str = "dataset/student_projects",
) -> dict:
    architecture, parsed_original = _load_original(run_dir, project_name)
    g_original = build_graph(parsed_original)

    input_path = Path(dataset_dir) / project_name / "input.txt"
    input_text = input_path.read_text(encoding="utf-8")

    scenarios = generate_scenarios(input_text, n=n_scenarios)

    scored = [_score_one_scenario(s, architecture, g_original, timeout) for s in scenarios]

    modifiability_score = sum(
        s["weighted_ged"] for s in scored if s.get("weighted_ged") is not None
    )
    by_magnitude: dict = {}
    for s in scored:
        if s.get("weighted_ged") is None:
            continue
        by_magnitude[s["magnitude"]] = by_magnitude.get(s["magnitude"], 0.0) + s["weighted_ged"]

    report = {
        "project": project_name,
        "n_scenarios": n_scenarios,
        "scenarios": scored,
        "modifiability_score": round(modifiability_score, 2),
        "by_magnitude": {k: round(v, 2) for k, v in by_magnitude.items()},
    }

    report_dir = Path(run_dir) / project_name / "modifiability"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run modifiability analysis for a project.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--n-scenarios", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    result = run(args.project, n_scenarios=args.n_scenarios, timeout=args.timeout)
    print(f"Modifiability Score for {args.project}: {result['modifiability_score']}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_modifiability.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add Evaluation/modifiability.py tests/test_modifiability.py
git commit -m "feat: add modifiability analysis orchestrator"
```

---

### Task 4: Streamlit frontend integration

**Files:**
- Create: `src/modifiability_frontend.py`
- Create: `tests/fixtures/modifiability_frontend_harness.py`
- Create: `tests/fixtures/modifiability_frontend_harness_empty.py`
- Test: `tests/test_modifiability_frontend.py`
- Modify: `app.py` (append one import + one function call; no existing lines changed)

**Interfaces:**
- Consumes: `Evaluation.modifiability.run` (Task 3), `proj_name` (str, already defined in `app.py` from the existing dataset-project dropdown).
- Produces: `render(project_name: str) -> None` (called once from the bottom of `app.py`).

- [ ] **Step 1: Write the failing tests**

Create `tests/fixtures/modifiability_frontend_harness.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modifiability_frontend import render

render(project_name="demo-project")
```

Create `tests/fixtures/modifiability_frontend_harness_empty.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modifiability_frontend import render

render(project_name="")
```

Create `tests/test_modifiability_frontend.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streamlit.testing.v1 import AppTest

from src import modifiability_frontend

HARNESS_PATH = str(Path(__file__).parent / "fixtures" / "modifiability_frontend_harness.py")
HARNESS_EMPTY_PATH = str(Path(__file__).parent / "fixtures" / "modifiability_frontend_harness_empty.py")


def test_render_shows_run_button_when_project_selected():
    at = AppTest.from_file(HARNESS_PATH)
    at.run()
    assert not at.exception
    button_labels = [b.label for b in at.button]
    assert "🔀 Run Modifiability Analysis" in button_labels


def test_render_shows_info_when_no_project_selected():
    at = AppTest.from_file(HARNESS_EMPTY_PATH)
    at.run()
    assert not at.exception
    button_labels = [b.label for b in at.button]
    assert "🔀 Run Modifiability Analysis" not in button_labels


def test_scenario_table_rows_formats_missing_values():
    rows = modifiability_frontend._scenario_table_rows([
        {"description": "Add X", "weight": 3, "magnitude": "small", "ged": 2.0, "exact": True, "weighted_ged": 6.0},
        {"description": "Add Y", "weight": 4, "magnitude": "large", "ged": None, "exact": False, "weighted_ged": None},
    ])
    assert rows[0]["GED"] == 2.0
    assert rows[1]["GED"] == "—"
    assert rows[1]["Weighted GED"] == "—"


def test_load_existing_report_reads_json(tmp_path):
    report_dir = tmp_path / "demo" / "modifiability"
    report_dir.mkdir(parents=True)
    (report_dir / "report.json").write_text('{"modifiability_score": 5.0}', encoding="utf-8")

    report = modifiability_frontend._load_existing_report("demo", run_dir=str(tmp_path))
    assert report == {"modifiability_score": 5.0}


def test_load_existing_report_returns_none_when_missing(tmp_path):
    report = modifiability_frontend._load_existing_report("demo", run_dir=str(tmp_path))
    assert report is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_modifiability_frontend.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.modifiability_frontend'`.

- [ ] **Step 3: Implement `src/modifiability_frontend.py`**

```python
"""
modifiability_frontend.py — Streamlit section for running modifiability
analysis on the currently-selected project. Appended to app.py without
modifying its existing logic.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from Evaluation.modifiability import run as run_modifiability

REPORT_RELATIVE_PATH = "modifiability/report.json"


def _load_existing_report(project_name: str, run_dir: str = "run") -> dict | None:
    report_path = Path(run_dir) / project_name / REPORT_RELATIVE_PATH
    if not report_path.exists():
        return None
    return json.loads(report_path.read_text(encoding="utf-8"))


def _scenario_table_rows(scenarios: list[dict]) -> list[dict]:
    """Convert scenario dicts into row dicts suitable for st.dataframe."""
    rows = []
    for s in scenarios:
        rows.append({
            "Description": s.get("description", ""),
            "Weight": s.get("weight"),
            "Magnitude": s.get("magnitude"),
            "GED": s.get("ged") if s.get("ged") is not None else "—",
            "Weighted GED": s.get("weighted_ged") if s.get("weighted_ged") is not None else "—",
            "Exact": s.get("exact", False),
        })
    return rows


def render(project_name: str) -> None:
    st.markdown("---")
    st.subheader("🔀 Modifiability Analysis")

    if not project_name:
        st.info("Select a project above to run modifiability analysis.")
        return

    regenerate = st.checkbox("🔄 Regenerate Analysis", value=False, key="chk_modifiability_regenerate")

    if st.button("🔀 Run Modifiability Analysis", key="btn_run_modifiability"):
        existing = _load_existing_report(project_name)
        report = None
        if existing and not regenerate:
            st.info("Using existing analysis. Check 'Regenerate Analysis' to force a fresh run.")
            report = existing
        else:
            try:
                with st.spinner(f"Analyzing modifiability for {project_name}…"):
                    report = run_modifiability(project_name)
                st.success(f"Analyzed {report['n_scenarios']} scenario(s).")
            except FileNotFoundError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Modifiability analysis failed: {e}")

        if report is not None:
            st.metric("Modifiability Score (lower = more flexible)", report["modifiability_score"])
            st.dataframe(_scenario_table_rows(report["scenarios"]), use_container_width=True)
            if report.get("by_magnitude"):
                st.markdown("#### By Magnitude")
                st.bar_chart(report["by_magnitude"])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_modifiability_frontend.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Wire into `app.py`**

Read `app.py` first to confirm its current end-of-file content (it should
currently end with the appended ADR section from prior work:
`render_adr_section(default_llm_model=llm_model)`). Append after that,
at the very end of the file:

```python

from src.modifiability_frontend import render as render_modifiability_section

render_modifiability_section(project_name=proj_name)
```

`proj_name` is already defined earlier in `app.py` from the existing
`st.selectbox("Select Dataset Project", ...)` call — do not redefine it, do
not touch any existing line.

- [ ] **Step 6: Manual smoke test**

Run: `streamlit run app.py`
Expected: page loads with no exceptions; scrolling to the bottom shows the
new "🔀 Modifiability Analysis" section below the existing ADR section;
selecting a project that has already been run through the diagram pipeline
and clicking "🔀 Run Modifiability Analysis" shows a spinner then either
results or a graceful `st.error` (depending on whether `LLM_API_KEY` is
configured and the LLM calls succeed) — never a raw traceback.

- [ ] **Step 7: Commit**

```bash
git add src/modifiability_frontend.py tests/fixtures/modifiability_frontend_harness.py tests/fixtures/modifiability_frontend_harness_empty.py tests/test_modifiability_frontend.py app.py
git commit -m "feat: surface modifiability analysis in the Streamlit UI"
```

---

## Self-Review

**Spec coverage:**
- Baseline graph from existing `component_diagram.puml` via `UMLParser` (spec §1) → Task 2/3. ✅
- Scenario generation with weight + magnitude (spec §2) → Task 1. ✅
- Per-scenario targeted architecture edit + render + parse + GED (spec §3) → Tasks 1-3. ✅
- Aggregation into `modifiability_score` + `by_magnitude` (spec §4) → Task 3. ✅
- No `src.diagram_agent`/openhands dependency (spec's corrected "3c") → Task 3, explicitly called out in Global Constraints. ✅
- Streamlit section, additive-only `app.py` (spec's Files section) → Task 4. ✅
- Per-scenario error handling, batch survives one failure (spec's Error handling) → Task 3, tested directly. ✅
- Environment note about broken base-env scipy → Global Constraints + Task 2 Step 5. ✅

**Placeholder scan:** No `TBD`/`TODO`/"implement later" strings; every code block is complete and runnable as written.

**Type consistency:** `generate_scenarios` (Task 1) returns `list[dict]` with keys `description`/`weight`/`magnitude`; Task 3's `_score_one_scenario` reads exactly those three keys via `scenario["description"]`/`scenario["weight"]`/`scenario["magnitude"]` — matches. `build_graph`/`compute_ged` (Task 2) signatures match exactly how Task 3 calls them. `run()`'s (Task 3) returned report shape (`project`, `n_scenarios`, `scenarios`, `modifiability_score`, `by_magnitude`) matches exactly what Task 4's `render()`/`_scenario_table_rows()` read.
