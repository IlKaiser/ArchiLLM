# Modifiability Analysis — Design

## Summary

A new evaluation dimension for ARTHUR: given a project already run through the
existing diagram pipeline (`run/{project}/architecture.json` +
`run/{project}/component_diagram.puml` present), generate N plausible future
scenarios from the project's user stories, have an LLM produce a minimally
modified architecture for each scenario, and measure how much the diagram
actually had to change using real graph edit distance (networkx). Scenarios
are weighted by importance; the weighted sum of edit distances is the
project's **Modifiability Score** — lower is better (less change required to
accommodate plausible future requirements = a more flexible architecture).

This mirrors the existing "Layer 2: Judge Scores" pattern (`arch_scorer.py`,
`adr_judge.py`) in spirit — lightweight, single-shot LLM calls, no openhands
Agent/sandboxing — but adds a purely computational step (graph edit distance)
that has nothing to do with an LLM.

## Precondition

Operates on a project that has *already* been run through the main diagram
pipeline: `run/{project}/architecture.json` and
`run/{project}/component_diagram.puml` must exist. If either is missing, the
orchestrator raises `FileNotFoundError` with a message telling the user to
run the diagram pipeline first — no fallback generation inside this feature.

## Pipeline

### 1. Baseline graph

Parse `run/{project}/component_diagram.puml` with the **existing**
`Evaluation.uml_parser.UMLParser` (`.parse(puml_text) -> {"nodes", "edges",
"leafnodes", "servicenodes"}`, already used by `metrics_calculator.py`). Build
a `networkx.DiGraph`: one node per entry in `nodes`, one directed edge per
`(src, dst)` in `edges`. This is `G_original`, computed once per project run
(not per scenario).

### 2. Scenario generation (one LLM call)

Input: the project's `dataset/.../input.txt` (system description + user
stories — same file the main pipeline reads). Output: a JSON list of exactly
`n_scenarios` (default 5) scenario objects:

```json
[
  {
    "description": "Support real-time push notifications for order status changes.",
    "weight": 4,
    "magnitude": "medium"
  }
]
```

- `weight`: integer 1-5, the LLM's estimate of how important/likely this
  future scenario is.
- `magnitude`: one of `"small"`, `"medium"`, `"large"` — the LLM's own
  estimate of how large a change this scenario would require. Used only for
  reporting/stratification (grouping results), never fed back into the
  weighted sum.

### 3. Per scenario

**3a. Targeted architecture edit (one LLM call).** Input: the existing
`architecture.json` (parsed dict) + one scenario's `description` + the
`KNOWLEDGE_BASE` pattern catalogue (same one `src/prompt.py` already
exports, for pattern-consistent modifications). Output: a full modified
`architecture.json`-shaped dict — the LLM is instructed to change/add only
what the scenario requires and leave everything else identical.

**3b. Render to PlantUML (one LLM call).** A new lightweight prompt
(`SCENARIO_RENDER_PROMPT`), modeled on `DIAGRAM_RENDER_PROMPT`'s formatting
rules (packages per pattern, `database` elements, labelled arrows, snake_case
aliases) but asking for the `.puml` text back directly in the response —
no file-writing tools, no openhands Agent, consistent with the ADR work's
"templated generation, not exploration" reasoning.

**3c. Parse + build graph.** `UMLParser().parse(rendered_text)` →
`G_modified` (same construction as `G_original`). **No dependency on
`src.diagram_agent`'s syntax-repair helpers**: that module imports the full
`openhands` SDK at import time (not installed in this environment, and not
a dependency this lightweight feature should force on anyone just to run
graph-edit-distance analysis). `UMLParser.parse()` already degrades
gracefully on malformed input (e.g. returns `{"nodes": [], "edges": []}` if
no `@startuml` is found, rather than raising) — combined with the
per-scenario try/except in step 4, a badly-rendered diagram for one scenario
just produces a `None`/inconclusive result for that scenario, not a crash.

**3d. Graph edit distance.**

```python
ged = nx.graph_edit_distance(
    G_original, G_modified,
    node_match=lambda a, b: a.get("label") == b.get("label"),
    timeout=timeout,  # default 10.0 seconds
)
```

Real networkx algorithm (exact, node-identity-aware via `node_match` so
nodes are only considered equal if they're literally the same named
component — otherwise every node pair would be freely substitutable at
default cost). Bounded by `timeout` so one large/pathological scenario can't
hang the whole run; if `graph_edit_distance` returns `None` (can happen if
the timeout elapses before any candidate is found) or the search doesn't
complete within budget, record `ged = None` for that scenario, flag it
`"exact": false` in the report, and exclude it from the aggregate sum
(logged as a warning, not silently dropped).

**3e. Weighted distance.** `weighted_ged = scenario["weight"] * ged` (only
for scenarios where `ged` is not `None`).

### 4. Aggregation

```json
{
  "project": "4-by-4",
  "n_scenarios": 5,
  "scenarios": [
    {"description": "...", "weight": 4, "magnitude": "medium", "ged": 3.0, "exact": true, "weighted_ged": 12.0}
  ],
  "modifiability_score": 47.5,
  "by_magnitude": {"small": 8.0, "medium": 12.0, "large": 27.5}
}
```

- `modifiability_score` = sum of `weighted_ged` over all scenarios with a
  non-null `ged`. **Lower is better** (a more modifiable/flexible
  architecture requires less change to satisfy plausible future
  requirements).
- `by_magnitude` = sum of `weighted_ged` grouped by each scenario's
  `magnitude` tag — lets you sanity-check that "large" scenarios really do
  produce larger weighted distances than "small" ones.

Written to `run/{project}/modifiability/report.json`.

## Files

- `Evaluation/modifiability_scenarios.py` (~120 lines) — `generate_scenarios`,
  `modify_architecture`, `render_scenario_diagram` (the three LLM-call
  functions + their prompt constants).
- `Evaluation/modifiability_graph.py` (~80 lines) — `build_graph(parsed:
  dict) -> nx.DiGraph`, `compute_ged(g1, g2, timeout) -> float | None`.
- `Evaluation/modifiability.py` (~100 lines) — orchestrator: `run(project_name:
  str, n_scenarios: int = 5, timeout: float = 10.0, run_dir: str = "run",
  dataset_dir: str = "dataset/student_projects") -> dict`. Raises
  `FileNotFoundError` per the precondition above. Writes and returns the
  report shown above.
- `src/modifiability_frontend.py` (~90 lines) — Streamlit section, appended
  to the bottom of `app.py` (after the existing `render_adr_section(...)`
  call — pure append, same additive-only discipline as the ADR frontend
  work). One button ("🔀 Run Modifiability Analysis") operating on the
  currently-selected project (`proj_name`, already in scope in `app.py`),
  showing: a table of scenarios (description/weight/magnitude/GED/weighted
  GED), the aggregate `modifiability_score`, and the `by_magnitude`
  breakdown. Idempotent/cached against `run/{project}/modifiability/report.json`
  the same way the ADR section caches against `docs/adr/`.
- Tests for each module, mocking all LLM calls (litellm.completion), using
  real `UMLParser`/`networkx` calls against small hand-written `.puml`
  fixtures (2-3 nodes) so GED computation is exercised for real, not mocked.

## Error handling (carried forward from the final ADR review's lessons)

- One scenario's LLM call failing (edit or render) or producing an
  unparseable diagram must not abort the whole batch: wrap steps 3a-3d in
  try/except per scenario, record `{"error": str(e)}` for that scenario in
  the report instead of crashing, and continue to the next scenario — same
  pattern as `Evaluation/adr_judge.py`'s per-ADR failure handling.
- The Streamlit button wraps `modifiability.run(...)` in try/except with
  `st.error(...)`, same pattern as `src/adr_frontend.py`.

## Environment note

`networkx.graph_edit_distance` depends on `scipy.optimize.linear_sum_assignment`
at runtime. The user's base conda environment currently has a broken `scipy`
install (`libgfortran.5.dylib` load failure — a pre-existing conda/homebrew
library conflict, unrelated to this feature). Verified that a clean pip venv
with `networkx==3.4.2` + `scipy` has no such issue. This feature must be
developed and tested in an isolated venv, not the base conda env; the base
env's `scipy` is a separate, pre-existing problem for the user to fix
independently if they want to run this outside a dedicated venv.

## Out of scope

- No changes to the main diagram pipeline, EffortRouter, or existing
  structural/judge metrics.
- No UI for editing scenario weights/magnitudes after generation — they're
  LLM-assigned and shown read-only.
- No batch/headless (`run_headless.py`) integration for this feature (per
  the earlier answer: new `Evaluation/` module + Streamlit section only).
- Graph edit distance uses `networkx.graph_edit_distance` directly — no
  custom approximation/metaheuristic layer of our own; `timeout` is
  networkx's own anytime-algorithm mechanism, not a separate search we
  implement.
