#!/usr/bin/env python3
"""
LLM-driven microservice pattern generator using LlamaIndex Workflow (Event-payload style).

Key points:
- Steps pass data via Event payloads (dicts), not Event subclasses — prevents attribute errors like _cancel_flag.
- Consumes StartEvent (engine kickoff), returns StopEvent (terminal).
- In-memory input (base64 ZIP via --payload-stdin/--payload-json).
- In-memory output (base64 ZIP to stdout/file).
- Optional pattern inference from README bullet lines.
- Model chosen via MODEL env var: openai/<model> or ollama/<model>.
"""
import asyncio
import os
import io
import re
import sys
import json
import argparse
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

# LlamaIndex workflow
from llama_index.core.workflow import Workflow, step, Context, Event, StartEvent, StopEvent
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI


# ==========================
# I/O Utilities
# ==========================

def unzip_to(z: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    with zipfile.ZipFile(z, "r") as zipf:
        zipf.extractall(dst)


def unzip_bytes(b: bytes, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    with zipfile.ZipFile(io.BytesIO(b), "r") as zipf:
        zipf.extractall(dst)


def copy_tree(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def zip_dir(src: Path, dst_zip: Path):
    if dst_zip.exists():
        dst_zip.unlink()
    with zipfile.ZipFile(dst_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in src.rglob("*"):
            z.write(p, p.relative_to(src))


def zip_dir_to_bytes(src_dir: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in Path(src_dir).rglob("*"):
            z.write(p, p.relative_to(src_dir))
    return buf.getvalue()


# ==========================
# Discovery & Config
# ==========================

def find_services(root: Path) -> List[Path]:
    services = []
    for p in root.iterdir():
        if p.is_dir() and (p / "src/main/java").exists():
            if list(p.rglob("*Application.java")):
                services.append(p)
    return services


def pkg_from_application(app_java: Path) -> str:
    parts = app_java.parts
    idx = parts.index("java")
    return ".".join(parts[idx + 1:-1])


def detect_package(service_dir: Path) -> str:
    app = next(service_dir.rglob("*Application.java"))
    return pkg_from_application(app)


def infer_service_name(folder_name: str) -> str:
    base = re.sub(r"-service$", "", folder_name)
    words = re.split(r"[-_ ]+", base)
    return "".join(w.capitalize() for w in words if w)


def read_text_if_exists(root: Path, rel: Optional[str]) -> str:
    if not rel:
        return ""
    p = root / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def load_roles_config(p: Optional[Path]) -> Dict[str, Any]:
    if not p:
        return {"defaults": {}, "services": {}}
    data = json.loads(Path(p).read_text(encoding="utf-8"))
    return {"defaults": data.get("defaults", {}), "services": data.get("services", {})}


def merge_cfg(defaults: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(defaults)
    if override:
        out.update(override)
    return out


# ==========================
# README pattern parsing
# ==========================

def canonical_name(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', s.lower())


def simplify_service_label(s: str) -> str:
    """Normalize a service display name like 'Authentication Service' → 'authentication'."""
    s = s.strip()
    # Strip markdown bold/italics if present
    s = re.sub(r"[*_`]+", "", s)
    # Remove trailing 'Service'
    s = re.sub(r"\bService\b", "", s, flags=re.IGNORECASE)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()

def _extract_patterns_freeform(text: str) -> dict:
    """
    Parse prose like:
      'Implements the Aggregate pattern and uses database-per-service for security.'
      'Uses Aggregate and Domain Event patterns, and database-per-service.'
      'Uses Aggregate, Saga, and Domain Event patterns, and database-per-service.'
      'Uses Aggregate and API Composition patterns, and database-per-service.'
    Returns a dict with flags.
    """
    t = text.lower()

    # canonicalize variants
    t = t.replace("domain events", "domain event")
    t = t.replace("events", "event")  # careful but fine for our keywords
    t = t.replace("api composition", "api composition")
    t = t.replace("database per service", "database-per-service")

    agg  = bool(re.search(r"\baggregate\b", t))
    de   = bool(re.search(r"\bdomain\s*event\b", t))
    saga = bool(re.search(r"\bsaga\b", t))
    api  = bool(re.search(r"\bapi\s*composition\b", t))

    # We don’t generate code for DB-per-service; track if you want it for docs/flags.
    dbps = bool(re.search(r"\bdatabase-?per-?service\b", t))

    return {
        "aggregate": agg,
        "events": de,
        "cqrs": False,                # not mentioned in this README style
        "saga": {"name": None} if saga else None,
        "api_composition": api,
        "database_per_service": dbps, # optional extra flag (harmless if unused)
    }

def parse_patterns_from_readme(readme_text: str) -> dict:
    """
    Supports BOTH styles:
      1) Bullets with parentheses:
         - Booking Service (Saga, Aggregate, Domain Event)
      2) Prose bullets with bold names:
         - **Authentication Service**: Handles ... Implements the Aggregate pattern ...
         - **Product Catalog Service**: ... Uses Aggregate and Domain Event patterns, and database-per-service.
    Returns mapping: { simplified_service_label: pattern_flags_dict }
    """
    patterns_map = {}

    lines = readme_text.splitlines()

    # --- Pass A: prose bullets with bold names and colon ---
    # e.g. "- **Authentication Service**: Handles ... Uses Aggregate and Domain Event patterns, and database-per-service."
    prose_bullet = re.compile(
        r"^\s*[-*•]\s*(?:\*\*|__)?\s*([A-Za-z0-9 &/_-]+?\s+Service)\s*(?:\*\*|__)?\s*:\s*(.+)$"
    )

    for line in lines:
        m = prose_bullet.match(line)
        if not m:
            continue
        raw_name = m.group(1).strip()
        desc = m.group(2).strip()
        name_key = simplify_service_label(raw_name)
        pats = _extract_patterns_freeform(desc)

        # Derive saga name if needed (first word of service)
        if pats.get("saga") and pats["saga"]["name"] is None:
            saga_name = raw_name.split()[0].title()
            pats["saga"]["name"] = saga_name

        patterns_map[name_key] = pats

    # --- Pass B: classic "(...)" bullets (keep backward compatibility) ---
    # e.g. "- Booking Service (Saga, Aggregate, Domain Event)"
    classic_bullet = re.compile(r"^\s*[-*•]\s*(.+?)\s*\(([^)]+)\)\s*$")

    for line in lines:
        m = classic_bullet.match(line)
        if not m:
            continue
        raw_name = m.group(1).strip()
        raw_patterns = m.group(2).strip()
        name_key = simplify_service_label(raw_name)
        # If already captured in Pass A, merge rather than overwrite
        existing = patterns_map.get(name_key, {
            "aggregate": False, "events": False, "cqrs": False, "saga": None, "api_composition": False
        })

        tokens = [t.strip().lower() for t in re.split(r"[,\uFF0C]+", raw_patterns)]
        for token in tokens:
            if token == "aggregate":
                existing["aggregate"] = True
            elif token in ("domain event", "event"):
                existing["events"] = True
            elif token == "cqrs":
                existing["cqrs"] = True
            elif token == "api composition":
                existing["api_composition"] = True
            elif token == "saga":
                if not existing.get("saga"):
                    existing["saga"] = {"name": raw_name.split()[0].title()}

        patterns_map[name_key] = existing

    return patterns_map



def match_readme_to_folders(readme_map: dict, service_folders: List[str]) -> dict:
    """
    Align README labels to actual service folders (best-effort fuzzy match).
    Returns: { folder_name: patterns_dict }
    """
    folder_keys = {}
    for f in service_folders:
        base = re.sub(r'-service$', '', f, flags=re.IGNORECASE)
        folder_keys[f] = canonical_name(base)

    assigned = {}
    for label, pats in readme_map.items():
        key = canonical_name(re.sub(r'\bservice\b', '', label))
        best = None
        best_score = -1
        for folder, fkey in folder_keys.items():
            score = 0
            if key in fkey or fkey in key:
                score += 5
            toks_l = set(re.findall(r'[a-z]+', label.lower()))
            toks_f = set(re.findall(r'[a-z]+', folder.replace('-', ' ').lower()))
            score += len(toks_l & toks_f)
            if score > best_score:
                best, best_score = folder, score
        if best:
            assigned[best] = pats
    return assigned


# ==========================
# LLM settings & prompts
# ==========================

SYSTEM_PROMPT = """You are an expert Java/Spring DDD architect. Generate minimal, correct Java code
that compiles with Spring Boot. Use package {package}, service {service_name}, patterns {patterns}.
Only use Spring Boot + JDK; add TODOs for integrations."""

PLAN_PROMPT = """Given the service context below, propose a list of Java files to generate
(with paths relative to src/main/java and a one-line purpose for each).

Context:
- Package: {package}
- Service Name: {service_name}
- Patterns: {patterns}
- README:
---
{readme}
---

Return JSON: {{ "files": [ {{"path": "path/ToFile.java", "purpose": "..."}}, ... ] }}"""

FILE_PROMPT = """Generate the full Java source code for this file.

Constraints:
- Package root: {package}
- Patterns: {patterns}
- Purpose: {purpose}
Return ONLY the Java code (no markdown).

File path: {relpath}"""

from dotenv import load_dotenv
assert load_dotenv()

def init_llm_from_env():
    model = os.getenv("MODEL", "openai/gpt-4.1")
    if model.startswith("openai/"):
        Settings.llm = OpenAI(model=model.split("/", 1)[1])
    else:
        Settings.llm = OpenAI(model=model)

# ==========================
# CUSTOM Events (one per step)
# ==========================

class StartPlanEvent(StartEvent):
    """Kickoff event carrying all inputs needed for planning."""
    service_dir: str
    package: str
    service_name: str
    patterns: dict
    readme: str
    output_service_dir: str


class PlanRequestEvent(Event):
    """What the planner consumes (same data as StartPlanEvent)."""
    service_dir: str
    package: str
    service_name: str
    patterns: dict
    readme: str
    output_service_dir: str


class PlanResultEvent(Event):
    """Planner output: a plan + original request."""
    plan: dict
    req: PlanRequestEvent


class FilesResultEvent(Event):
    """Codegen output: rendered files (path+code) + original request."""
    files: list  # [{ "path": "...", "code": "..." }]
    req: PlanRequestEvent


class DoneEvent(StopEvent):
    """Terminal event; return from final step to stop the workflow."""
    status: str = "ok"


# ==========================
# Workflow
# ==========================

class CodegenWorkflow(Workflow):
    """
    Route:
      StartPlanEvent -> bootstrap -> plan_service -> generate_files -> write_files -> DoneEvent
    """

    @step()
    async def bootstrap(self, ev: StartEvent) -> PlanRequestEvent:
        # Convert StartPlanEvent to PlanRequestEvent (one Event-typed input, one Event-typed output)
        return PlanRequestEvent(
            service_dir=ev.service_dir,
            package=ev.package,
            service_name=ev.service_name,
            patterns=ev.patterns,
            readme=ev.readme,
            output_service_dir=ev.output_service_dir,
        )

    @step()
    async def plan_service(self, ev: PlanRequestEvent) -> PlanResultEvent:
        llm = Settings.llm
        sysm = ChatMessage(
            role=MessageRole.SYSTEM,
            content=SYSTEM_PROMPT.format(
                package=ev.package,
                service_name=ev.service_name,
                patterns=json.dumps(ev.patterns),
            ),
        )
        usr = ChatMessage(
            role=MessageRole.USER,
            content=PLAN_PROMPT.format(
                package=ev.package,
                service_name=ev.service_name,
                patterns=json.dumps(ev.patterns),
                readme=ev.readme,
            ),
        )
        resp = await llm.achat(messages=[sysm, usr])
        txt = resp.message.content
        try:
            plan = json.loads(txt)
            print("Plan:", plan)
        except Exception:
            i, j = txt.find("{"), txt.rfind("}")
            plan = json.loads(txt[i:j + 1]) if i != -1 and j != -1 else {"files": []}
        return PlanResultEvent(plan=plan, req=ev)

    @step()
    async def generate_files(self, ev: PlanResultEvent) -> FilesResultEvent:
        llm = Settings.llm
        out = []
        for f in ev.plan.get("files", []):
            relpath = f.get("path")
            purpose = f.get("purpose", "")
            sysm = ChatMessage(
                role=MessageRole.SYSTEM,
                content=SYSTEM_PROMPT.format(
                    package=ev.req.package,
                    service_name=ev.req.service_name,
                    patterns=json.dumps(ev.req.patterns),
                ),
            )
            usr = ChatMessage(
                role=MessageRole.USER,
                content=FILE_PROMPT.format(
                    package=ev.req.package,
                    patterns=json.dumps(ev.req.patterns),
                    purpose=purpose,
                    relpath=relpath,
                ),
            )
            resp = await llm.achat(messages=[sysm, usr])
            print("Generated file:", relpath)
            code = resp.message.content.strip()
            out.append({"path": relpath, "code": code})
        return FilesResultEvent(files=out, req=ev.req)

    @step()
    async def write_files(self, ev: FilesResultEvent) -> StopEvent:
        root = Path(ev.req.output_service_dir) / "src/main/java"
        print("Writing files to:", root)
        for f in ev.files:
            dst = root / f["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            code = f["code"]
            if not code.lstrip().startswith("package "):
                code = f"package {ev.req.package};\n\n" + code
            dst.write_text(code, encoding="utf-8")
        return StopEvent(status="ok")



# ==========================
# Payload helpers (in-memory input/output)
# ==========================

def load_payload(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def base64_decode(s: str) -> bytes:
    import base64
    return base64.b64decode(s)


def base64_encode(b: bytes) -> str:
    import base64
    return base64.b64encode(b).decode("utf-8")


def process_payload(payload: dict, work_dir: Path):
    """
    Accepts a dict:
      { "filename": "...", "zip_base64": "<...>" }
    Extracts into work_dir.
    """
    b64 = payload.get("zip_base64", "")
    if not b64:
        raise SystemExit("payload JSON missing 'zip_base64'")
    unzip_bytes(base64_decode(b64), work_dir)


# ==========================
# CLI
# ==========================

async def add_pattern(zip_json):
    # Prepare working copy
    output_dir = Path("output_project")
    work = Path("old_project_work")
    process_payload(zip_json, work)

    # Load README and discover services
    readme = read_text_if_exists(work, "Readme.md")
    services = find_services(work)

    # Optionally derive patterns from README (fallback to roles for non-matched)
    readme_patterns = parse_patterns_from_readme(readme)
    print("README patterns:", readme_patterns)
    readme_assignments = match_readme_to_folders(readme_patterns, [s.name for s in services]) if readme_patterns else {}
    roles = {"defaults": {}, "services": {}}

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    copy_tree(work, output_dir)

    # Init LLM
    init_llm_from_env()

    # Run per service
    for svc in services:
        cfg = (readme_assignments.get(svc.name)) \
              or merge_cfg(roles.get("defaults", {}), roles.get("services", {}).get(svc.name, {}))

        package = detect_package(output_dir / svc.name)
        service_name = infer_service_name(svc.name)

        req = {
            "service_dir": str(svc),
            "package": package,
            "service_name": service_name,
            "patterns": cfg,
            "readme": readme,
            "output_service_dir": str(output_dir / svc.name),
        }

        print("Processing service:", svc.name, "with config:", json.dumps(cfg))
        print("req:", req)
        wf = CodegenWorkflow(timeout=1200)
        # Start the workflow by emitting a StartEvent with our request as payload
        await wf.run(**req)


    # In-memory base64 JSON output (optional)
    
    blob = zip_dir_to_bytes(output_dir)
    payload = {"filename": "augmented_project.zip", "zip_base64": base64_encode(blob)}
    
    return payload


async def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=False)
    src.add_argument("--input-zip", type=Path)
    src.add_argument("--input-dir", type=Path)

    ap.add_argument("--payload-json", type=Path, help="Path to JSON with {filename, zip_base64}")
    ap.add_argument("--payload-stdin", action="store_true", help="Read payload JSON from STDIN")

    ap.add_argument("--output-dir", type=Path, required=True, help="Where to write the augmented project")
    ap.add_argument("--zip-output", type=Path, help="Optional: zip the augmented project here")
    ap.add_argument("--emit-zip-base64-stdout", action="store_true", help='Emit {"filename","zip_base64"} JSON to STDOUT')
    ap.add_argument("--emit-zip-base64-file", type=Path, help="Write the same JSON to this file")
    ap.add_argument("--output-filename", type=str, default="augmented_project.zip", help="Filename used inside JSON payload")

    ap.add_argument("--roles-config", type=Path, required=False, help="JSON config with defaults/services (fallback)")
    ap.add_argument("--readme-path", type=str, default="README.md", help="README path inside project root")
    ap.add_argument("--infer-patterns-from-readme", action="store_true", help="Derive patterns from README instead of JSON roles")
    ap.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()

    # Prepare working copy
    work = Path(str(args.output_dir) + "__work")

    # Input priority: payload-stdin > payload-json > input-zip > input-dir
    if args.payload_stdin:
        payload = json.loads(sys.stdin.read())
        process_payload(payload, work)
    elif args.payload_json:
        payload = load_payload(args.payload_json)
        process_payload(payload, work)
    elif args.input_zip:
        unzip_to(args.input_zip, work)
    elif args.input_dir:
        copy_tree(args.input_dir, work)
    else:
        raise SystemExit("Provide one of --payload-stdin, --payload-json, --input-zip, or --input-dir")

    # Load README and discover services
    readme = read_text_if_exists(work, args.readme_path)
    services = find_services(work)

    # Optionally derive patterns from README (fallback to roles for non-matched)
    readme_patterns = parse_patterns_from_readme(readme)
    print("README patterns:", readme_patterns)
    readme_assignments = match_readme_to_folders(readme_patterns, [s.name for s in services]) if readme_patterns else {}
    roles = load_roles_config(args.roles_config)

    if args.dry_run:
        print("Services:", [s.name for s in services])
        for s in services:
            cfg = (readme_assignments.get(s.name) if args.infer_patterns_from_readme else None) \
                  or merge_cfg(roles.get("defaults", {}), roles.get("services", {}).get(s.name, {}))
            print(f" - {s.name}: {json.dumps(cfg)}")
        return

    # Copy working tree to output (we write files there)
    if args.output_dir.exists():
        shutil.rmtree(args.output_dir)
    copy_tree(work, args.output_dir)

    # Init LLM
    init_llm_from_env()

    # Run per service
    for svc in services:
        cfg = (readme_assignments.get(svc.name)) \
              or merge_cfg(roles.get("defaults", {}), roles.get("services", {}).get(svc.name, {}))

        package = detect_package(args.output_dir / svc.name)
        service_name = infer_service_name(svc.name)

        req = {
            "service_dir": str(svc),
            "package": package,
            "service_name": service_name,
            "patterns": cfg,
            "readme": readme,
            "output_service_dir": str(args.output_dir / svc.name),
        }

        print("Processing service:", svc.name, "with config:", json.dumps(cfg))
        print("req:", req)
        wf = CodegenWorkflow(timeout=1200)
        # Start the workflow by emitting a StartEvent with our request as payload
        await wf.run(**req)

    # File-based zip output (optional)
    if args.zip_output:
        zip_dir(args.output_dir, args.zip_output)

    # In-memory base64 JSON output (optional)
    if args.emit_zip_base64_stdout or args.emit_zip_base64_file:
        blob = zip_dir_to_bytes(args.output_dir)
        payload = {"filename": args.output_filename, "zip_base64": base64_encode(blob)}
        if args.emit_zip_base64_stdout:
            print(json.dumps(payload))
        if args.emit_zip_base64_file:
            args.emit_zip_base64_file.write_text(json.dumps(payload), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
