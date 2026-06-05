# ARTHUR — Architecture Through Hybrid UML Reasoning

ARTHUR is a research framework that automatically generates **PlantUML component diagrams** from natural-language project requirements (PRDs). It uses multi-agent LLM pipelines (via the OpenHands SDK) to extract microservice architectures and render them as structured UML diagrams, then evaluates the quality of those diagrams against ground-truth references.

## Overview

Given a project's `input.txt` (system description + user stories), ARTHUR:

1. **Extracts** the microservice architecture into a structured `architecture.json`
2. **Renders** it as a PlantUML component diagram (`component_diagram.puml`) + Markdown summary
3. **Evaluates** the diagram against a ground-truth reference using structural metrics and an LLM-as-a-judge

## Project Structure

```text
ARCHILLMv2/
├── src/
│   ├── diagram_agent.py       # Two-agent pipeline: Extractor → Renderer (→ Syntax Fixer)
│   ├── prompt.py              # Prompt templates + microservice pattern knowledge base
│   ├── effort_router.py       # EffortRouter: routes turns between primary/secondary LLM
│   ├── local_llm.py           # Local inference helpers (Ollama / HuggingFace TGI / vLLM)
│   └── main.py                # Batch CLI over dataset/student_projects/
├── Evaluation/
│   ├── metrics_calculator.py  # Node F1, Edge F1, GED, Boundary Accuracy
│   ├── llm_judge.py           # LLM alignment judge (matched pairs, boundary correctness)
│   └── arch_scorer.py         # LLM rubric scorer (completeness, accuracy, rationality, readability)
├── app.py                     # Streamlit GUI (project picker, live logs, eval dashboard)
├── run_headless.py            # Headless batch runner with CSV reporting + charts
├── repo_to_puml.py            # Bootstrap: fetch GitHub repos → generate input.txt / diagram.puml
├── dataset/student_projects/  # Input dataset (one folder per project, contains input.txt + ref.wsd)
├── MicroserviceDataset/       # Dataset built from GitHub repos via repo_to_puml.py
├── run/                       # Generated outputs (component_diagram.puml, architecture.json, …)
├── Dockerfile                 # Ubuntu 22.04 + Miniconda + env_name conda env
├── docker-compose.yml         # Streamlit UI + headless runner + Laminar telemetry stack
├── environment.yml            # Conda environment definition
└── headless_report.csv        # Auto-generated evaluation report
```

## Getting Started

### Prerequisites

- [Conda](https://docs.conda.io/en/latest/) or Docker
- An LLM API key (Anthropic, OpenAI-compatible, or a local Ollama/vLLM server)

### Environment Variables

Copy `.env.template` to `.env` and fill in:

```bash
# Primary LLM for diagram generation
LLM_API_KEY=<your-key>
LLM_MODEL=anthropic/claude-sonnet-4-5-20250929   # any LiteLLM-compatible model string
LLM_BASE_URL=                                     # leave blank for cloud; set for local/proxy

# Secondary LLM (used by EffortRouter in multi-agent mode)
SECONDARY_LLM_API_KEY=<your-key>
SECONDARY_LLM_MODEL=openhands/devstral-medium-2507

# LLM-as-a-judge (evaluation only)
LLM_JUDGE_KEY=<your-key>
LLM_JUDGE_URL=https://api.openai.com/v1
JUDGE_MODEL=gpt-4o

# Laminar observability (optional)
LMNR_PROJECT_API_KEY=
```

### Option A: Docker Compose (Recommended)

```bash
docker compose build
docker compose up -d          # starts Streamlit UI + Laminar stack
```

- **Streamlit UI**: `http://localhost:8501`
- **Laminar traces**: `http://localhost:5667`

### Option B: Local Conda

```bash
conda env create -f environment.yml
conda activate env_name
streamlit run app.py
```

---

## Usage

### Streamlit GUI

```bash
streamlit run app.py          # or: docker compose up agent-orchestrator
```

Select a project, optionally enable **Multi-Agent (EffortRouter)** or **Validation Agent**, then click **Run Diagram Pipeline**. The sidebar also has a **⚡ Use Local Model** toggle for Ollama/HuggingFace inference.

### Headless Batch Runner

`run_headless.py` processes an entire dataset directory, writes results to a CSV, and optionally generates evaluation charts.

```bash
# Basic: generate diagrams for all projects
python run_headless.py --dataset dataset/student_projects --output ./run

# With evaluation (structural metrics + LLM judge)
python run_headless.py --dataset dataset/student_projects --output ./run --eval

# Evaluate only (skip generation, re-use existing outputs)
python run_headless.py --dataset dataset/student_projects --output ./run \
  --eval-only --metrics all

# Run LLM judge only (preserves existing structural metrics in CSV)
python run_headless.py --dataset dataset/student_projects --output ./run \
  --eval-only --metrics judge

# Single project
python run_headless.py --dataset dataset/student_projects --output ./run \
  --project my-project --eval

# Generate charts from an existing report
python run_headless.py --charts-only --report headless_report.csv
```

**Key flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--dataset` | `MicroserviceDataset` | Dataset directory |
| `--output` | `./run` | Output directory for generated files |
| `--report` | `headless_report.csv` | CSV report path |
| `--max-cost` | `50.0` | Stop when pipeline cost exceeds this ($) |
| `--eval` | off | Run evaluation after generation |
| `--eval-only` | off | Skip generation, only run evaluation |
| `--metrics` | `all` | `ged`, `structural`, `judge`, or `all` |
| `--multi-agent` | off | Enable EffortRouter delegation |
| `--skip-existing` | off | Skip projects that already have outputs |
| `--force` | off | Regenerate even if outputs exist |
| `--visualize` | off | Generate charts after run |

### Docker Compose — Headless Runner

```bash
# Default run (all projects, cloud LLM from .env)
docker compose run --rm headless

# With evaluation and multi-agent
HEADLESS_EXTRA_ARGS="--eval --metrics all --multi-agent" docker compose run --rm headless

# Ollama local inference (Ollama running on host)
LOCAL_BACKEND=ollama LOCAL_MODEL=qwen2.5-coder:32b \
  LOCAL_BASE_URL=http://host.docker.internal:11434 \
  docker compose run --rm headless
```

### Local Model Inference

Both the CLI and the Streamlit sidebar support local inference via **Ollama** or **HuggingFace TGI / vLLM**:

```bash
# Ollama
python run_headless.py --dataset dataset/student_projects --output ./run \
  --local-backend ollama --local-model qwen2.5-coder:32b

# vLLM / HuggingFace TGI
python run_headless.py --dataset dataset/student_projects --output ./run \
  --local-backend huggingface \
  --local-model mistralai/Mistral-7B-Instruct-v0.3 \
  --local-url http://localhost:8080
```

> Local models run with `native_tool_calling=False` and `temperature=0.7`. The evaluation judge always uses the cloud LLM configured via `LLM_JUDGE_KEY`.

---

## Dataset Bootstrap — `repo_to_puml.py`

Automatically build a dataset from GitHub repositories:

```bash
# Generate diagram + requirements.txt for a repo
python repo_to_puml.py https://github.com/org/repo

# Generate input.txt in PRD format (SYSTEM DESCRIPTION + USER STORIES)
python repo_to_puml.py --input-txt https://github.com/org/repo

# Generate ONLY input.txt (skip diagram generation)
python repo_to_puml.py --input-txt-only https://github.com/org/repo

# Process a list of repos from a file
python repo_to_puml.py --input-txt-only --file repos.txt --out ./MicroserviceDataset
```

The generated `input.txt` follows the format expected by the diagram pipeline:

```
# SYSTEM DESCRIPTION:
<paragraph describing the system>

# USER STORIES:
1. As a <role>, I want <capability> so that <benefit>.
2. ...
```

Requires `ANTHROPIC_API_KEY` and optionally `GITHUB_TOKEN` (raises rate limit from 60 → 5000 req/h).

---

## Evaluation

ARTHUR evaluates generated diagrams on two axes:

**Structural metrics** (computed via LLM alignment + graph comparison):
- **Node F1** — precision/recall of matched microservice nodes
- **Edge F1** — precision/recall of matched dependency edges
- **GED** — Graph Edit Distance (normalised)
- **Boundary Accuracy** — fraction of nodes placed in the correct architectural boundary

**LLM Judge scores** (0–10 rubric via `arch_scorer.py`):
- **Completeness** — coverage of functional requirements
- **Accuracy** — correctness of architectural decisions
- **Rationality** — coherence of design choices
- **Readability** — clarity and navigability of the diagram

Results are written to `headless_report.csv` and visualised as bar charts + a radar chart (`--visualize`).

---

## Laminar Telemetry (Optional)

The `docker-compose.yml` includes a self-hosted [Laminar](https://www.lmnr.ai/) stack for tracing agent executions.

```bash
docker compose up -d
```

1. Open `http://localhost:5667`, create a project, copy the **Project API Key**
2. Add to `.env`: `LMNR_PROJECT_API_KEY=<key>`
3. Restart: `docker compose restart agent-orchestrator`

View full agent traces, LLM call latencies, token counts, and tool invocations at `http://localhost:5667`.
