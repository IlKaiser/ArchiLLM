# Archi Dataset
This folder contains datasets used for the **ArchiLLM** project, organized into two main categories: **student projects** and **open-source projects**.  
Each dataset provides structured information to support **microservice architecture modeling**, **analysis**, and **LLM-based reasoning**.

---

## 📁 Folder Structure

```
dataset/
├── student_projects/
│ ├── ProjectA/
│ │ ├── input.txt
│ │ ├── student_doc.md
│ │ └── DataMetrics.json
│ ├── ProjectB/
│ │ ├── input.txt
│ │ ├── student_doc.md
│ │ └── DataMetrics.json
│ └── ...
└── open_source_projects/
├── ProjectX/
│ ├── input.txt
│ └── endpoint.csv
├── ProjectY/
│ ├── input.txt
│ └── endpoint.csv
└── ...
```

---

## 🧩 Folder Categories

### 1. `student_projects/`

Contains datasets developed by students as part of academic or research projects.  
Each project folder includes:

- **`input.txt`** — a summary of the project, outlining key objectives, technologies, and architectural focus.  
- **`student_doc.md`** — detailed documentation describing the project’s architecture, rationale, and design decisions.  
- **`DataMetrics.json`** — structured data describing the **microservice architecture**, including metrics such as:
  - Number of services  
  - Dependencies between components  
  - API communication patterns  
  - Coupling and cohesion indicators  

Together, these files provide a rich source for both **quantitative** and **qualitative** architectural analysis.

---

### 2. `open_source_projects/`

Contains datasets derived from **open-source repositories**, used for benchmarking and comparative studies.  
Each open-source project includes:

- **`input.txt`** — a short textual summary describing the project’s main features and scope.  
- **`endpoint.csv`** — a structured list of **extracted API endpoints** (method, path, and service), used for endpoint-level architectural and behavioral analysis.  

## 🔗 Download and Citation

You can download the complete dataset directly from Zenodo:

📦 **[Download ArchiLLM Dataset on Zenodo](https://doi.org/10.5281/zenodo.14238664)**  
📘 **DOI:** [10.5281/zenodo.14238664](https://doi.org/10.5281/zenodo.14238664)

To cite this dataset in your work:

> Calamo, M. *et al.* (2025). **ArchiLLM Dataset** [Data set]. Zenodo.  
> DOI: [10.5281/zenodo.14238664](https://doi.org/10.5281/zenodo.14238664)
