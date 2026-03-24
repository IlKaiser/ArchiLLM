# ARTHUR

This repository provides ARTHUR (Architecture Refactoring Through Hybrid UML Reasoning): an automated scaffolding and project generation framework powered by LLM agents. Using the `openhands` SDK, it orchestrates AI agents to autonomously construct backend services (Java Spring Boot or Python), modern frontends, and comprehensive test suites based on simple text descriptions.

## Overview

The core of the system resides in the `src/` directory, orchestrating agent execution across multiple projects defined in the `projects/` folder. It reads project requirements, delegates tasks to specialized LLM agents, and tracks the cost and execution time of each generation cycle.

### Key Components

- **`src/main.py`**: The primary entry point. It scans the `projects/` directory, reads project descriptions from `desc.txt` files, and triggers the agent sequence for each valid project. It maintains an execution log (`execution_report.csv`) to track runtimes and API costs.
- **`app.py`**: A Streamlit Web GUI orchestrator that provides a visual dashboard for the configuration of API keys, model parameters, and dynamic backend generation inputs (.xmp models or Java DAOs).
- **`src/agent.py`**: Defines the `openhands` agent configurations and workflows. It orchestrates three generation phases: Backend, Frontend, and Tests.
- **`src/aggregate_tests.py`**: A utility script that traverses all generated projects to locate test reports (both custom JSON reports and standard JUnit XML Surefire reports). It outputs a consolidated, easy-to-read summary of test results and pass rates across all projects.

## Project Structure

```text
ARTHUR/
├── src/
│   ├── main.py                # Main orchestrator script
│   ├── agent.py               # AI Agent definitions and task delegation
│   ├── prompt.py              # Prompt templates for generation
│   └── aggregate_tests.py     # Aggregates test results across projects
├── app.py                     # Streamlit frontend application
├── Dockerfile                 # Base image wrapping all openhands dependencies
├── docker-compose.yml         # Compose configuration exposing port 8501
├── projects/                  # Directory containing distinct projects
│   ├── [project_name]/        # Individual project folder
│   │   └── desc.txt           # Natural language description of the project
│   └── ...
├── environment.yml            # Conda environment definition
└── execution_report.csv       # Automatically generated runtime and cost logs
```

## Getting Started

### Prerequisites

You need [Conda](https://docs.conda.io/en/latest/) installed on your machine.
Ensure you have set the appropriate environment variables for the LLM (e.g., `LLM_API_KEY` for Anthropic/Claude). You can define these in a `.env` file at the root of the project.

### Setup & Usage

You can run the application directly from your local Conda environment, or via Docker (Highly Recommended).

#### Option A: Docker Compose (Recommended Setup)
Docker safely encapsulates the Java, Maven, Node.js, and Conda dependencies required for the OpenHands AI agents to autonomously build and compile applications without affecting your host system.

```bash
docker-compose build
docker-compose up
```
*Note: This will securely spin up the Python environment and instantly launch the Streamlit frontend. Open your browser to `http://localhost:8501` to view and use the application.*

#### Option B: Local Conda Environment Setup
Create and activate the conda environment:

```bash
conda env create -f environment.yml
# Please swap "env_name" for your specific local active environment if developing
conda activate env_name
```

**1. Streamlit Dashboard (GUI)**
The easiest way to orchestrate generation manually is using the new Streamlit frontend:
```bash
streamlit run app.py
```
This handles dynamic file uploads (models, DAOs, code), live agent terminal stdout tracking, and bundles a downloadable `.zip` file of the result.

**2. Generating Projects (CLI)**

To run the agent orchestrator broadly across all projects defined in the `projects/` folder:

```bash
python src/main.py
```
*Note: `main.py` contains a `SKIP_LIST` array. Projects listed there will be bypassed during execution.*

**2. Aggregating Test Results**

Once projects and their tests have been generated and executed, you can view a consolidated summary of the test results:

```bash
python src/aggregate_tests.py
```

This will print a tabular summary of total tests, passed tests, failed tests, and the overall pass rate for each project.
