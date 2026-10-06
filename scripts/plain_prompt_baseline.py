#!/usr/bin/env python3
"""Plain-prompt baseline: one LLM call per project, no agents, no pattern
knowledge base, no validation/repair loop — just "here are the description and
user stories, write a PlantUML component diagram". Gives the ARCHI pipeline a
naive reference point on the same dataset.

Fully standalone: stdlib only, imports nothing from this repo (no src/ agents,
prompts or PlantUML repair) — the diagram is the model's raw output, only
extracted from the reply and rendered. Writes per project, under --output/<project>/:
  component_diagram.puml   extracted @startuml..@enduml block
  component_diagram.png    rendered via the public PlantUML server
  raw_response.md          the model's full reply, for auditing
plus prompt.txt at the output root, and a run-progress JSON (phase
"plain_prompt_baseline") that dashboard/generate.py picks up like any other run
(run `python dashboard/generate.py` afterwards to refresh index.html).

Usage:
  python scripts/plain_prompt_baseline.py \
    --dataset dataset/student_projects \
    --output results/deepseek_plain_baseline/student_projects \
    --progress-file dashboard/run_progress/deepseek-plain-baseline.json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import time
import zlib
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

REPO = Path(__file__).resolve().parent.parent
PLANTUML_SERVER = "https://www.plantuml.com/plantuml/png/"

logger = logging.getLogger(__name__)

PROMPT = (
    "Create a PlantUML component diagram of a microservice architecture that applies "
    "the appropriate microservice patterns, starting from the system description and "
    "user stories below. Reply with the complete PlantUML source in a single "
    "```plantuml code block (from @startuml to @enduml).\n\n"
    "{spec}"
)
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"


def load_dotenv(path: Path) -> None:
    """Minimal .env loader (KEY=VALUE lines); never overrides the real environment."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def chat(base_url: str, api_key: str, model: str, prompt: str, timeout: float) -> dict:
    """Single chat-completion call against an OpenAI-compatible endpoint."""
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def extract_puml(text: str) -> str | None:
    match = re.search(r"@startuml.*?@enduml", text, re.S)
    return match.group(0).strip() + "\n" if match else None


def plantuml_encode(text: str) -> str:
    """PlantUML server text encoding: raw deflate + PlantUML's base64 alphabet."""
    data = zlib.compress(text.encode("utf-8"))[2:-4]
    charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    out = []
    for i in range(0, len(data), 3):
        b = data[i:i + 3] + bytes(3 - len(data[i:i + 3]))
        n = (b[0] << 16) | (b[1] << 8) | b[2]
        out.append("".join(charset[(n >> shift) & 0x3F] for shift in (18, 12, 6, 0)))
    return "".join(out)


def render_png(puml_path: Path, attempts: int = 3) -> bool:
    """Render puml_path to a sibling .png via the public PlantUML server.

    Retries with backoff, falling back to curl: the public server intermittently
    rejects valid requests, and some CDN edges refuse long URLs from urllib.
    """
    url = PLANTUML_SERVER + plantuml_encode(puml_path.read_text(encoding="utf-8"))
    png_path = puml_path.with_suffix(".png")
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (plain-prompt-baseline)"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                png_path.write_bytes(resp.read())
            return True
        except (urllib.error.URLError, OSError):
            try:
                subprocess.run(["curl", "-fsSL", url, "-o", str(png_path)], check=True, timeout=30,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except (subprocess.SubprocessError, OSError):
                if attempt < attempts:
                    time.sleep(3 * attempt)
    logger.warning("PNG render failed for %s", puml_path)
    return False


class Progress:
    """Writes the same run-progress schema as run_headless.RunProgress."""

    def __init__(self, path: Path, projects: list[str], args: argparse.Namespace, model: str):
        self.path, self.lock = path, Lock()
        now = datetime.now(timezone.utc).isoformat()
        self.state = {
            "schema_version": 1, "run_id": path.stem, "phase": "plain_prompt_baseline",
            "status": "running", "pid": os.getpid(), "started_at": now, "updated_at": now,
            "finished_at": None, "dataset": args.dataset, "output": args.output, "report": None,
            "backend": "cloud", "model": model, "total": len(projects),
            "projects": [{"name": n, "status": "pending", "time_seconds": None, "cost": None, "error": None}
                         for n in projects],
        }
        self.write()

    def update(self, name: str, status: str, **fields) -> None:
        with self.lock:
            entry = next(p for p in self.state["projects"] if p["name"] == name)
            entry.update(status=status, **fields)
            if status == "running":
                entry["started_at"] = datetime.now(timezone.utc).isoformat()
            self.write()

    def finish(self) -> None:
        with self.lock:
            failed = any(p["status"] == "error" for p in self.state["projects"])
            self.state["status"] = "failed" if failed else "complete"
            self.state["finished_at"] = datetime.now(timezone.utc).isoformat()
            self.write()

    def write(self) -> None:
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)


def run_project(name: str, args: argparse.Namespace, api_key: str, progress: Progress) -> None:
    out_dir = REPO / args.output / name
    puml_path = out_dir / "component_diagram.puml"
    if args.skip_existing and puml_path.is_file():
        progress.update(name, "skipped")
        return
    progress.update(name, "running")
    start = time.monotonic()
    try:
        spec = (REPO / args.dataset / name / "input.txt").read_text(encoding="utf-8")
        reply = chat(args.base_url, api_key, args.model, PROMPT.format(spec=spec), args.timeout)
        content = reply["choices"][0]["message"]["content"] or ""
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "raw_response.md").write_text(content, encoding="utf-8")
        puml = extract_puml(content)
        if puml is None:
            raise ValueError("no @startuml..@enduml block in the reply")
        puml_path.write_text(puml, encoding="utf-8")
        rendered = render_png(puml_path)
        usage = reply.get("usage") or {}
        progress.update(
            name, "success", time_seconds=round(time.monotonic() - start, 2),
            prompt_tokens=usage.get("prompt_tokens"), completion_tokens=usage.get("completion_tokens"),
            error=None if rendered else "PlantUML render failed (puml saved)",
        )
    except (OSError, ValueError, KeyError, urllib.error.URLError) as e:
        logger.error("%s failed: %s", name, e)
        progress.update(name, "error", time_seconds=round(time.monotonic() - start, 2), error=str(e)[:300])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", default="dataset/student_projects")
    parser.add_argument("--output", default="results/deepseek_plain_baseline/student_projects")
    parser.add_argument("--progress-file", default="dashboard/run_progress/deepseek-plain-baseline.json")
    parser.add_argument("--model", default=os.getenv("PLAIN_BASELINE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.getenv("PLAIN_BASELINE_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--project", help="Comma-separated project name(s); default all")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    load_dotenv(REPO / ".env")
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY (or LLM_API_KEY) is not set")

    dataset = REPO / args.dataset
    projects = sorted(p.name for p in dataset.iterdir() if (p / "input.txt").is_file())
    if args.project:
        wanted = {p.strip() for p in args.project.split(",")}
        projects = [p for p in projects if p in wanted]

    (REPO / args.output).mkdir(parents=True, exist_ok=True)
    (REPO / args.output / "prompt.txt").write_text(PROMPT, encoding="utf-8")
    progress = Progress(REPO / args.progress_file, projects, args, f"deepseek/{args.model}")
    logger.info("Plain-prompt baseline: %d projects, model=%s", len(projects), args.model)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda name: run_project(name, args, api_key, progress), projects))
    progress.finish()
    logger.info("Done: %s", progress.state["status"])


if __name__ == "__main__":
    main()
