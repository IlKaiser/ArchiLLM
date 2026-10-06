"""Service-only view of a generated architecture.

Builds a reduced PlantUML component diagram from ``architecture.json`` that
keeps only the microservice decomposition: one component per microservice and
one edge per service-to-service dependency. Datastores, pattern groupings and
external actors are left out, so the diagram shows the extraction result alone
(which services exist and how they talk), independent of how the full diagram
was laid out.

Deterministic — no LLM call — so it can be produced during a run (opt-in via
``run_headless.py --services-view`` or the GUI checkbox) or backfilled later:

    python src/services_view.py results/<run>/<dataset>            # every project
    python src/services_view.py results/<run>/<dataset>/<project>  # one project
"""
from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

SERVICES_PUML = "component_diagram_services.puml"

__all__ = ["SERVICES_PUML", "build_services_puml", "write_services_view"]


def _alias(name: str) -> str:
    """PlantUML-safe alias: word characters only, never starting with a digit."""
    alias = re.sub(r"\W+", "_", name.strip()).strip("_") or "service"
    return f"s_{alias}" if alias[0].isdigit() else alias


def build_services_puml(arch: dict) -> str | None:
    """Render the service-only PlantUML for an architecture.json dict.

    Returns None when the architecture declares no microservices.
    """
    services = [m["name"] for m in arch.get("microservices", []) if m.get("name")]
    if not services:
        return None
    known = set(services)
    edges: dict[tuple[str, str], set[str]] = {}
    for dep in arch.get("dependencies", []):
        src, dst = dep.get("from"), dep.get("to")
        if src in known and dst in known and src != dst:
            protocol = (dep.get("protocol") or "").strip()
            edges.setdefault((src, dst), set()).update([protocol] if protocol else [])

    title = arch.get("system") or "Architecture"
    lines = ["@startuml", f"title {title} — services view", "skinparam componentStyle rectangle", ""]
    lines += [f'component "{name}" as {_alias(name)}' for name in services]
    lines.append("")
    for (src, dst), protocols in sorted(edges.items()):
        label = f" : {', '.join(sorted(protocols))}" if protocols else ""
        lines.append(f"{_alias(src)} --> {_alias(dst)}{label}")
    lines += ["", "@enduml", ""]
    return "\n".join(lines)


def write_services_view(project_dir: str | Path) -> Path | None:
    """Write component_diagram_services.puml next to the project's architecture.json.

    Returns the written path, or None if there is no usable architecture.json.
    """
    arch_path = Path(project_dir) / "architecture.json"
    try:
        arch = json.loads(arch_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning("services view skipped, unreadable %s: %s", arch_path, e)
        return None
    puml = build_services_puml(arch) if isinstance(arch, dict) else None
    if puml is None:
        return None
    out = Path(project_dir) / SERVICES_PUML
    out.write_text(puml, encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(argv) != 1:
        print(__doc__)
        return 2
    root = Path(argv[0])
    project_dirs = [root] if (root / "architecture.json").is_file() else sorted(
        p for p in root.iterdir() if p.is_dir())
    written = [p for p in map(write_services_view, project_dirs) if p]
    logger.info("wrote %d services view(s) under %s", len(written), root)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
