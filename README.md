# MultiMultiAgent-ArchiLLM

This repository provides an automated scaffolding and project generation framework powered by LLM agents. Using the `openhands` SDK, it orchestrates AI agents to autonomously construct backend services (Java Spring Boot or Python), modern frontends, and comprehensive test suites based on simple text descriptions.

## Overview

The core of the system resides in the `src/` directory, orchestrating agent execution across multiple projects defined in the `projects/` folder. It reads project requirements, delegates tasks to specialized LLM agents, and tracks the cost and execution time of each generation cycle.

### Key Components

- **`src/main.py`**: The primary entry point. It scans the `projects/` directory, reads project descriptions from `desc.txt` files, and triggers the agent sequence for each valid project. It maintains an execution log (`execution_report.csv`) to track runtimes and API costs.
- **`src/agent.py`**: Defines the `openhands` agent configurations and workflows. It orchestrates three generation phases: Backend, Frontend, and Tests.
- **`src/aggregate_tests.py`**: A utility script that traverses all generated projects to locate test reports (both custom JSON reports and standard JUnit XML Surefire reports). It outputs a consolidated, easy-to-read summary of test results and pass rates across all projects.

## Project Structure

```text
MultiMultiAgent-ArchiLLM/
├── src/
│   ├── main.py                # Main orchestrator script
│   ├── agent.py               # AI Agent definitions and task delegation
│   ├── prompt.py              # Prompt templates for generation
│   └── aggregate_tests.py     # Aggregates test results across projects
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

### Setup

Create and activate the conda environment:

```bash
conda env create -f environment.yml
conda activate env_name
```

### Usage

**1. Generating Projects**

To run the agent orchestrator across all projects defined in the `projects/` folder:

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
