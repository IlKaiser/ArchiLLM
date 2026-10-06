#!/usr/bin/env python3
"""Score several systems' architecture views on R2ABench with ONE evaluator.

Every configuration (ARCHI, the plain-prompt baseline, R2ABench's released
workflows) is parsed, aligned and judged by exactly the same code, judge model
and node-selection rule, so the resulting numbers are comparable with each
other — not with the R2ABench paper's own tables (different judge and metrics).

A view counts as valid (R2ABench L0-style) only if it exists, parses to at least one
node, and renders on the PlantUML server; invalid views are excluded from means and
reported as a validity rate.

Two views per prediction:
  full      every leaf node of the diagram, aligned against the reference's
            leaf nodes; Node/Edge F1, GED score, boundary accuracy + rubric.
  services  service nodes only (role-classified by the judge model, the same
            way for predictions and references); edges lifted to the
            enclosing service. Scored only on R2A-MS projects, i.e. those whose
            reference itself has >= MS_MIN_SERVICES services.

Commands (run in order; LLM responses are cached under <out>/cache):
  freeze-ms   classify reference views, write <out>/r2a_ms_projects.csv
  score       score every configuration, write <out>/scores.csv
  summarize   aggregate tables + calibration against R2ABench's cohort.csv

    uv run --with openai --with networkx --with pandas --with python-dotenv \\
        python Evaluation/cross_eval.py freeze-ms|score|summarize
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import logging
import os
import contextlib
import time
import urllib.error
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from arch_scorer import ArchScorer  # noqa: E402
from llm_judge import LLMJudge  # noqa: E402
from metrics_calculator import MetricsCalculator  # noqa: E402
from uml_parser import UMLParser  # noqa: E402

logger = logging.getLogger(__name__)
REPO = Path(__file__).resolve().parent.parent
MS_MIN_SERVICES = 3
SUBSETS = {"E-R2A": "E-R2A", "G-R2A": "G-R2A-52"}  # dataset subset -> R2ABench Output folder
R2A_OUT = "R2ABench 2/Output/{r2a_subset}/{workflow}/deepseek-v4.1-flash/{project}/predicted.puml"
DEFAULT_CONFIGS = {
    "arthur": "results/arthur_r2a/deepseek_flash/{subset}/{project}/component_diagram.puml",
    "plain-prompt": "results/plain_r2a/deepseek_flash/{subset}/{project}/component_diagram.puml",
    **{f"r2a-{wf}": R2A_OUT.replace("{workflow}", wf)
       for wf in ("direct", "metagpt-custom", "mini-swe-agent", "openhands")},
}
ROLES = ("service", "datastore", "infrastructure", "pattern_group", "layer_or_group",
         "actor", "external_system", "client_ui", "other")
ROLE_PROMPT = """You label the nodes of a software architecture diagram by role.
Roles:
- service: an independently deployable backend application/service that owns a business
  capability (a microservice or standalone backend service/server application).
- datastore: database, cache, file/object store, search index, event store.
- infrastructure: API gateway, proxy, load balancer, message broker/queue/bus, service
  registry/discovery, config server, monitoring/logging, orchestration/runtime platform.
- pattern_group: a container named after a design pattern (Saga, CQRS, Database per Service...).
- layer_or_group: a layer, tier, package, module group or environment that only groups others.
- actor: human user or role.
- external_system: third-party or out-of-scope system.
- client_ui: frontend, mobile/web client, UI component.
- other: anything else, including in-process modules, classes, libraries and functions.
Node names use "Parent::Child" paths. Answer ONLY with JSON: {{"roles": {{"<node>": "<role>"}}}}
covering every node exactly as given.

Nodes:
{nodes}"""


class Evaluator:
    """Judge-backed scoring with a content-addressed response cache."""

    def __init__(self, out: Path):
        load_dotenv(REPO / ".env")
        self.key = os.getenv("LLM_JUDGE_KEY") or os.getenv("LLM_API_KEY")
        self.url = os.getenv("LLM_JUDGE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("JUDGE_MODEL", "gpt-5.6-luna").split("/")[-1]
        self.cache = out / "cache"
        self.client = OpenAI(api_key=self.key, base_url=self.url)

    def _cached(self, kind: str, payload: str, compute):
        digest = hashlib.sha256(f"{kind}|{self.model}|{payload}".encode()).hexdigest()[:24]
        path = self.cache / kind / f"{digest}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        result = compute()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
        return result

    def roles(self, nodes: list[str]) -> dict[str, str]:
        def compute():
            resp = self.client.chat.completions.create(
                model=self.model, response_format={"type": "json_object"},
                messages=[{"role": "user", "content": ROLE_PROMPT.format(nodes="\n".join(nodes))}])
            raw = json.loads(resp.choices[0].message.content).get("roles", {})
            return {n: raw.get(n, "other") if raw.get(n) in ROLES else "other" for n in nodes}
        return self._cached("roles", "\n".join(sorted(nodes)), compute)

    def renders(self, puml: str) -> bool:
        """L0-style validity: the PlantUML server renders it without a syntax error.

        A 400 is retried because the public server occasionally rejects valid input.
        """
        def compute():
            url = "https://www.plantuml.com/plantuml/svg/" + plantuml_encode(puml)
            for attempt in range(3):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cross-eval)"})
                    with urllib.request.urlopen(req, timeout=60):
                        return {"renders": True}
                except urllib.error.HTTPError as e:
                    if e.code != 400:
                        raise
                    time.sleep(3 * (attempt + 1))
            return {"renders": False}
        return self._cached("render", puml, compute)["renders"]

    def align(self, prd: str, gt_nodes: list[str], pred_nodes: list[str]) -> dict:
        def compute():
            result = LLMJudge(self.key, self.url, self.model).evaluate_alignment(prd, gt_nodes, pred_nodes)
            result.pop("_usage", None)
            return result
        return self._cached("align", json.dumps([prd, sorted(gt_nodes), sorted(pred_nodes)]), compute)

    def rubric(self, prd: str, puml: str) -> dict:
        def compute():
            result = ArchScorer(self.key, self.url, self.model).score(prd_text=prd, predicted_puml=puml) or {}
            result.pop("_usage", None)
            return ArchScorer.extract_scores(result)
        return self._cached("rubric", json.dumps([prd, puml]), compute)


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


def parse(text: str) -> dict:
    with contextlib.redirect_stdout(io.StringIO()):
        return UMLParser().parse(text)


def services_view(parsed: dict, roles: dict[str, str]) -> dict:
    """Reduce a parsed diagram to its service nodes and service-to-service edges.

    An endpoint inside a service (e.g. its Lambda or DB) is lifted to that
    service. Dependencies mediated by infrastructure (A -> broker/gateway -> B)
    count as A -> B, so architectures that talk through a queue or gateway are
    not scored as having no service dependencies. Same rule for every system.
    """
    def bare(node: str) -> str:
        # The parser names top-level nodes "Global::X" but their children "X::Y".
        return node[len("Global::"):] if node.startswith("Global::") else node

    services = sorted(n for n in parsed["nodes"] if roles.get(n) == "service")
    infra = {bare(n) for n in parsed["nodes"] if roles.get(n) == "infrastructure"}

    def owner(node: str, candidates) -> str | None:
        b = bare(node)
        hits = [c for c in candidates if b == bare(c) or b.startswith(f"{bare(c)}::")]
        return max(hits, key=lambda c: len(bare(c))) if hits else None

    lifted = [(owner(a, services), owner(b, services), owner(a, infra), owner(b, infra))
              for a, b in parsed["edges"]]
    edges = {(sa, sb) for sa, sb, _, _ in lifted if sa and sb}
    into_infra, out_of_infra = {}, {}
    for sa, sb, ia, ib in lifted:
        if sa and ib and not sb:
            into_infra.setdefault(ib, set()).add(sa)
        if ia and sb and not sa:
            out_of_infra.setdefault(ia, set()).add(sb)
    for hub, sources in into_infra.items():
        edges |= {(a, b) for a in sources for b in out_of_infra.get(hub, ())}
    edges = sorted((a, b) for a, b in edges if a != b)
    return {"nodes": services, "leafnodes": services, "servicenodes": services, "edges": edges}


def metrics(name: str, gt: dict, pred: dict, alignment: dict) -> dict:
    calc = MetricsCalculator()
    with contextlib.redirect_stdout(io.StringIO()):
        calc.evaluate_project(name, gt, pred, alignment)
    r = calc.results[0]
    return {k: r[k] for k in ("Node_F1", "Edge_F1", "GED", "Boundary_Accuracy")}


def projects(dataset: Path) -> list[tuple[str, str]]:
    return [(s, p.name) for s in SUBSETS for p in sorted((dataset / s).iterdir()) if (p / "ref.wsd").is_file()]


def freeze_ms(ev: Evaluator, dataset: Path, out: Path) -> None:
    rows = []
    for subset, project in projects(dataset):
        ref = parse((dataset / subset / project / "ref.wsd").read_text(errors="ignore"))
        n_services = sum(r == "service" for r in ev.roles(ref["nodes"]).values())
        rows.append({"subset": subset, "project": project, "ref_services": n_services,
                     "r2a_ms": n_services >= MS_MIN_SERVICES})
    write_csv(out / "r2a_ms_projects.csv", rows)
    logger.info("R2A-MS: %d of %d projects (>= %d reference services)",
                sum(r["r2a_ms"] for r in rows), len(rows), MS_MIN_SERVICES)


def score_one(ev: Evaluator, dataset: Path, ms: set, config: str, template: str,
              subset: str, project: str) -> list[dict]:
    base = {"config": config, "subset": subset, "project": project, "r2a_ms": (subset, project) in ms}
    pred_path = REPO / template.format(subset=subset, r2a_subset=SUBSETS[subset], project=project)
    text = pred_path.read_text(errors="ignore") if pred_path.is_file() else ""
    pred = parse(text) if "@startuml" in text else {"nodes": []}
    if not pred.get("nodes") or not ev.renders(text):
        return [{**base, "view": "full", "valid": False, "missing": not text}]
    proj_dir = dataset / subset / project
    prd = (proj_dir / "input.txt").read_text(encoding="utf-8")
    gt = parse((proj_dir / "ref.wsd").read_text(errors="ignore"))
    rows = []
    align = ev.align(prd, gt["leafnodes"] or gt["nodes"], pred["leafnodes"] or pred["nodes"])
    rows.append({**base, "view": "full", "valid": True, **metrics(project, gt, pred, align),
                 **ev.rubric(prd, text)})
    if base["r2a_ms"]:
        gt_s, pred_s = services_view(gt, ev.roles(gt["nodes"])), services_view(pred, ev.roles(pred["nodes"]))
        align_s = ev.align(prd, gt_s["nodes"], pred_s["nodes"]) if pred_s["nodes"] else \
            {"matched_pairs": [], "unmatched_gt_nodes": gt_s["nodes"], "unmatched_predicted_nodes": []}
        rows.append({**base, "view": "services", "valid": True, "pred_services": len(pred_s["nodes"]),
                     "ref_services": len(gt_s["nodes"]), **metrics(project, gt_s, pred_s, align_s)})
    return rows


def score(ev: Evaluator, dataset: Path, out: Path, configs: dict, workers: int,
          only: set[str] | None = None, scores_name: str = "scores.csv") -> None:
    ms_file = out / "r2a_ms_projects.csv"
    if not ms_file.is_file():
        raise SystemExit("run freeze-ms first: the R2A-MS subset must be fixed before scoring")
    ms = {(r["subset"], r["project"]) for r in csv.DictReader(open(ms_file)) if r["r2a_ms"] == "True"}
    jobs = [(c, t, s, p) for c, t in configs.items() for s, p in projects(dataset) if not only or p in only]

    def run(job):
        try:
            return score_one(ev, dataset, ms, *job)
        except Exception as e:  # one failed judge call must not sink the batch; it is recorded
            logger.error("%s/%s/%s failed: %s", job[0], job[2], job[3], e)
            return [{"config": job[0], "subset": job[2], "project": job[3], "view": "full",
                     "valid": None, "error": str(e)[:200]}]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = [r for batch in pool.map(run, jobs) for r in batch]
    write_csv(out / scores_name, rows)
    logger.info("scored %d jobs -> %s", len(jobs), out / scores_name)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("freeze-ms", "score", "summarize"))
    parser.add_argument("--dataset", default="dataset/R2A")
    parser.add_argument("--out", default="results/r2a_cross_eval")
    parser.add_argument("--config", action="append", default=[],
                        help="name=path_template (repeatable); default: ARCHI, plain prompt, 4 R2A workflows")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--project", help="Comma-separated project names to score (smoke tests); "
                                          "writes scores_subset.csv so the full table is never overwritten")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    dataset, out = REPO / args.dataset, REPO / args.out
    configs = dict(c.split("=", 1) for c in args.config) or DEFAULT_CONFIGS
    if args.command == "summarize":
        from cross_eval_summary import summarize
        summarize(out, REPO / "R2ABench 2/Results/cohort.csv")
        return
    ev = Evaluator(out)
    logger.info("judge model: %s", ev.model)
    if args.command == "freeze-ms":
        freeze_ms(ev, dataset, out)
    else:
        only = {p.strip() for p in args.project.split(",")} if args.project else None
        score(ev, dataset, out, configs, args.workers, only, "scores_subset.csv" if only else "scores.csv")


if __name__ == "__main__":
    main()
