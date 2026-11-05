"""Render ArchiLLM (v1) outputs as PlantUML component diagrams.

ArchiLLM wrote one JSON per project (microservices, datastores and pattern
groups with a rationale) and no diagram, so the diagram-based judges of
Evaluation/student_cross_eval.py cannot score it directly. This script draws
exactly what the JSON states, with ARCHI's diagram conventions:

  * every microservice once, inside the package of the first pattern group
    that lists it (a "Microservices" package if none does);
  * every datastore, inside its owner's package when it has exactly one
    associated service, linked to each associated service by a plain line;
  * one note per pattern group with ArchiLLM's own explanation;
  * no inter-service dependencies, because ArchiLLM emits none.

The JSONs are read from the old ArchiLLM release (git branch ``main``,
results/old/results_claude, Claude Sonnet 4.5).

    python scripts/archillm_to_puml.py [--ref main] [--out results/archillm_v1/student_projects]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import textwrap
from pathlib import Path

logger = logging.getLogger(__name__)
REPO = Path(__file__).resolve().parent.parent
SRC_DIR = "results/old/results_claude"


def _alias(name: str, used: set[str]) -> str:
    base = re.sub(r"\W+", "_", name.strip().lower()).strip("_") or "node"
    alias, i = base, 2
    while alias in used:
        alias, i = f"{base}_{i}", i + 1
    used.add(alias)
    return alias


def _label(text: str) -> str:
    return text.replace('"', "'").strip()


def render(project: str, out: dict) -> str:
    """PlantUML for one ArchiLLM output (``output`` field of its JSON)."""
    services = [s["name"].strip() for s in out.get("microservices", []) if s.get("name")]
    used: set[str] = set()
    svc_alias = {s: _alias(s, used) for s in services}
    groups = out.get("patterns", [])
    primary: dict[str, str] = {}
    for g in groups:
        for s in g.get("involved_microservices", []):
            if s in svc_alias and s not in primary:
                primary[s] = f"{g.get('implementation_pattern', '').strip()} ({g.get('group_name', '').strip()})"
    stores = out.get("datastore", [])
    store_alias = {i: _alias(d.get("datastore_name", f"store_{i}"), used) for i, d in enumerate(stores)}
    owned: dict[str, list[int]] = {}
    shared: list[int] = []
    for i, d in enumerate(stores):
        owners = [s for s in d.get("associated_microservices", []) if s in svc_alias]
        if len(owners) == 1:
            owned.setdefault(owners[0], []).append(i)
        else:
            shared.append(i)

    lines = ["@startuml", f"title {project} - Microservices Component Diagram (ArchiLLM)", "",
             "skinparam componentStyle rectangle", "skinparam packageStyle rectangle",
             "skinparam shadowing false", ""]
    packages: dict[str, list[str]] = {}
    for s in services:
        packages.setdefault(primary.get(s, "Microservices"), []).append(s)
    for pkg, members in packages.items():
        lines.append(f'package "{_label(pkg)}" {{')
        for s in members:
            lines.append(f'  [{_label(s)}] as {svc_alias[s]}')
            for i in owned.get(s, []):
                lines.append(f'  database "{_label(stores[i].get("datastore_name", ""))}" as {store_alias[i]}')
        lines.append("}")
        lines.append("")
    for i in shared:
        lines.append(f'database "{_label(stores[i].get("datastore_name", ""))}" as {store_alias[i]}')
    lines.append("")
    for i, d in enumerate(stores):
        for s in d.get("associated_microservices", []):
            if s in svc_alias:
                lines.append(f"{svc_alias[s]} -- {store_alias[i]}")
    lines.append("")
    for g in groups:
        members = [s for s in g.get("involved_microservices", []) if s in svc_alias]
        if not members:
            continue
        head = f"**{_label(g.get('implementation_pattern', ''))}** ({_label(g.get('group_name', ''))})"
        body = textwrap.wrap(_label(g.get("explaination") or g.get("explanation") or ""), 70)
        who = "Participants: " + ", ".join(svc_alias[s] for s in members)
        lines += [f"note bottom of {svc_alias[members[0]]}", f"  {head}",
                  *[f"  {w}" for w in textwrap.wrap(who, 70)], *[f"  {b}" for b in body], "end note", ""]
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ref", default="main", help="git ref holding the ArchiLLM release")
    parser.add_argument("--out", type=Path, default=REPO / "results" / "archillm_v1" / "student_projects")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    names = subprocess.run(["git", "ls-tree", "--name-only", args.ref, f"{SRC_DIR}/"],
                           capture_output=True, text=True, check=True, cwd=REPO).stdout.split()
    written = 0
    for name in names:
        project = Path(name).stem
        if project == "summary":
            continue
        data = json.loads(subprocess.run(["git", "show", f"{args.ref}:{name}"], capture_output=True,
                                         text=True, check=True, cwd=REPO).stdout)
        out = data.get("output") or {}
        if not out.get("microservices"):
            logger.warning("%s: empty ArchiLLM output, skipped", project)
            continue
        target = args.out / project / "component_diagram.puml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(project, out), encoding="utf-8")
        written += 1
    logger.info("wrote %d diagrams to %s", written, args.out)


if __name__ == "__main__":
    main()
