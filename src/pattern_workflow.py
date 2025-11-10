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
import nest_asyncio

# Core Python imports
import asyncio
import os
import io
import re
import sys
import json
import shutil
import zipfile
import base64
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Core llama_index imports - wrapped in try/except to handle missing stubs
# and different package versions gracefully
try:
    from llama_index.core import Settings, VectorStoreIndex, StorageContext, load_index_from_storage
    from llama_index.core.workflow import Workflow, step, Event, StartEvent, StopEvent
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.readers.github import GithubRepositoryReader, GithubClient
    from llama_index.llms.openai import OpenAI
    from llama_index.llms.anthropic import Anthropic
    from llama_index.llms.mistralai import MistralAI
    from llama_index.core.llms import ChatMessage, MessageRole
except ImportError as e:
    print(f"Warning: Some llama_index imports failed ({e}). Functionality may be limited.")

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


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
# Note: CLI entrypoint removed. Use add_pattern(zip_json, archi_payload=...) programmatically.
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

def load_patterns_from_archi(archi_json: dict) -> dict:
    """
    Convert an in-memory Archi JSON payload into the same per-service pattern
    mapping used by the workflow.

    Input (example):
    {
      "microservices": [ { "name": "Booking Service" }, ... ],
      "patterns": [ { "implementation_pattern": "Saga", "involved_microservices": ["Booking Service", ...], "name": "BookingSaga" }, ... ],
      "datastore": [ ... ]
    }

    Returns: { simplified_service_label: patterns_dict }
    where patterns_dict contains keys: aggregate, events, cqrs, saga, api_composition, database_per_service
    """
    out: Dict[str, Dict[str, Any]] = {}

    def _name_of(x: Any) -> str:
        if isinstance(x, dict):
            return (x.get("name") or "").strip()
        if isinstance(x, str):
            return x.strip()
        return str(x)

    # Seed services from microservices list when available
    for ms in archi_json.get("microservices", []):
        raw_name = _name_of(ms)
        key = simplify_service_label(raw_name)
        out[key] = {
            "aggregate": False,
            "events": False,
            "cqrs": False,
            "saga": None,
            "api_composition": False,
            "database_per_service": False,
        }

    # Walk patterns and set flags on involved services
    for pat in archi_json.get("patterns", []):
        impl = (pat.get("implementation_pattern") or "").lower()
        involved = pat.get("involved_microservices") or pat.get("involved_services") or []
        # Normalize involved list to strings (safe default if name missing)
        involved = [_name_of(s) for s in involved]

        # Derive a saga name if present
        saga_name = pat.get("name") or None

        for svc in involved:
            key = simplify_service_label(svc)
            if key not in out:
                out[key] = {
                    "aggregate": False,
                    "events": False,
                    "cqrs": False,
                    "saga": None,
                    "api_composition": False,
                    "database_per_service": False,
                }

            if "aggregate" in impl:
                out[key]["aggregate"] = True
            if "domain event" in impl or "event" in impl:
                out[key]["events"] = True
            if "cqrs" in impl:
                out[key]["cqrs"] = True
            if "saga" in impl:
                # prefer explicit name, otherwise derive from service
                if not saga_name:
                    saga_name = svc.split()[0].title() if svc else None
                # Use None when no saga name is available to keep the field type consistent (dict | None)
                out[key]["saga"] = {"name": saga_name} if saga_name else None
            if "api composition" in impl or "api-composition" in impl or "api composition" in impl:
                out[key]["api_composition"] = True
            if "database" in impl or "database-per-service" in impl or "database per service" in impl:
                out[key]["database_per_service"] = True

    return out

def match_labels_to_folders(label_map: dict, service_folders: List[str]) -> dict:
    """
    Best-effort align a mapping keyed by human-friendly labels (or simplified labels)
    to actual folder names found in the project.

    Returns: { folder_name: patterns_dict }
    """
    folder_keys = {}
    for f in service_folders:
        base = re.sub(r'-service$', '', f, flags=re.IGNORECASE)
        folder_keys[f] = canonical_name(base)

    assigned = {}
    for label, pats in label_map.items():
        # label might already be simplified; derive a canonical key
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

SYSTEM_PROMPT = """You are an expert Java/Spring DDD architect. Generate minimal, correct Java stub
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

assert load_dotenv()

def init_llm_from_env():
    model = os.getenv("MODEL", "openai/gpt-4.1")
    if model.startswith("openai"):
        Settings.llm = OpenAI(model="gpt-4.1", temperature=0, timeout=9999.0)
    elif model.startswith("mistral"):
        Settings.llm = MistralAI(model="mistral-large-2411", temperature=0, timeout=9999.0, max_tokens=19000)
    elif model.startswith("anthropic") or model.startswith("claude"):
        # anthropic/<model> or claude/<model>
        Settings.llm = Anthropic(model="claude-haiku-4-5",temperature=1.0, max_tokens=64000, timeout=9999.0)
    else:
        Settings.llm = OpenAI(model="gpt-4.1", temperature=0, timeout=9999.0)
    
    print("The model being used is:", model)


# Optional: GitHub RAG support
GITHUB_RETRIEVER = None

async def build_github_retriever(
    github_token: Optional[str],
    owner: str = "microservices-patterns",
    repo: str = "ftgo-application",
    branch: str = "master",
    include_dirs: Optional[List[str]] = None,
    force_rebuild: bool = False
):
    """Build and return a LlamaIndex retriever for a GitHub repository.

    Example usage:
        retriever = await build_github_retriever(os.getenv("GITHUB_TOKEN"))
        docs = retriever.retrieve("Where are the pattern examples for sagas?")

    The function will set Settings.embed_model to OpenAIEmbedding using the
    current OPENAI_API_KEY if available.

    Args:
        github_token: GitHub API token
        owner: Repository owner
        repo: Repository name
        branch: Branch name
        include_dirs: List of directories to include (None for all)
        force_rebuild: If True, rebuild index even if cached version exists
    """
    global GITHUB_RETRIEVER
    if not github_token:
        raise ValueError("github_token is required to read private or API-rate-limited repos")
        
    # Setup cache directory
    cache_dir = Path(".cache/github_indexes")
    cache_dir.mkdir(parents=True, exist_ok=True)
    persist_dir = cache_dir / f"{owner}_{repo}_{branch}"
    
    # Try to load cached index if it exists and force_rebuild is False
    if not force_rebuild and persist_dir.exists():
        try:
            print(f"Loading cached index from {persist_dir}")
            # Ensure embeddings are configured
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                Settings.embed_model = OpenAIEmbedding(api_key=openai_api_key)
            # Load the index from disk using the storage context
            storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))
            index = load_index_from_storage(storage_context)
            retriever = index.as_retriever(similarity_top_k=5)
            GITHUB_RETRIEVER = retriever
            print("Successfully loaded cached index")
            return retriever
        except Exception as e:
            print(f"Failed to load cached index: {e}, rebuilding...")

    github_client = GithubClient(github_token=github_token, verbose=False)

    # Default filters: include no specific directories (read whole repo) but exclude binary/docs
    filter_directories: Tuple[List[str], GithubRepositoryReader.FilterType]
    if include_dirs is None:
        # include all directories
        filter_directories = ([], GithubRepositoryReader.FilterType.EXCLUDE)
    else:
        filter_directories = (include_dirs, GithubRepositoryReader.FilterType.INCLUDE)

    filter_file_extensions = (
        [
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".ico",
            "json",
            ".ipynb",
        ],
        GithubRepositoryReader.FilterType.EXCLUDE,
    )

    reader = GithubRepositoryReader(
        github_client=github_client,
        owner=owner,
        repo=repo,
        use_parser=False,
        verbose=True,
        filter_directories=filter_directories,
        filter_file_extensions=filter_file_extensions,
    )

    print(f"Loading repository {owner}/{repo} (branch={branch}) via GitHub API")
    documents = reader.load_data(branch=branch)
    print(f"Loaded {len(documents)} documents from GitHub repository")

    # Ensure embeddings are configured (use OPENAI_API_KEY if set)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        Settings.embed_model = OpenAIEmbedding(api_key=openai_api_key)

    # Build an in-memory vector index
    index = VectorStoreIndex.from_documents(documents)
    
    # Save the index to disk for future use
    try:
        print(f"Saving index to {persist_dir}")
        index.storage_context.persist(persist_dir=str(persist_dir))
        print("Successfully saved index to disk")
    except Exception as e:
        print(f"Warning: Failed to save index to disk: {e}")
    
    retriever = index.as_retriever(similarity_top_k=5)
    GITHUB_RETRIEVER = retriever
    return retriever

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


class ExamplesRetrievedEvent(Event):
    """Holds the plan, the original request and a single RAG context string retrieved once."""
    plan: dict
    req: PlanRequestEvent
    rag_context: str


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
    async def retrieve_examples(self, ev: PlanResultEvent) -> ExamplesRetrievedEvent:
        """Run GitHub RAG once for the whole plan/pattern set and return a single context blob.

        This avoids per-file retrieval and reduces API calls. The result is attached as
        rag_context and passed to the next step (generate_files).
        """
        rag_context = ""
        if GITHUB_RETRIEVER:
            try:
                # Build a single query describing the service and its patterns
                query = f"Examples for service {ev.req.service_name} with patterns: {json.dumps(ev.req.patterns)}"
                nodes = GITHUB_RETRIEVER.retrieve(query)
                if nodes:
                    rag_context = "\n\nRelevant examples from reference implementation:\n"
                    for node in nodes:
                        # node may be NodeWithScore or similar; try .text then .node_text
                        text = getattr(node, 'text', None) or getattr(node, 'node_text', None) or str(node)
                        rag_context += f"\n{text}\n"
            except Exception as e:
                print(f"Warning: GitHub RAG retrieval failed: {e}")
        return ExamplesRetrievedEvent(plan=ev.plan, req=ev.req, rag_context=rag_context)

    @step()
    async def generate_files(self, ev: ExamplesRetrievedEvent) -> FilesResultEvent:
        llm = Settings.llm
        out = []
        for f in ev.plan.get("files", []):
            relpath = f.get("path")
            purpose = f.get("purpose", "")
            # Use the single rag_context retrieved earlier (possibly empty)
            rag_context = ev.rag_context or ""
            
            sysm = ChatMessage(
                role=MessageRole.SYSTEM,
                content=SYSTEM_PROMPT.format(
                    package=ev.req.package,
                    service_name=ev.req.service_name,
                    patterns=json.dumps(ev.req.patterns),
                ) + rag_context,
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
    return base64.b64decode(s)


def base64_encode(b: bytes) -> str:
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

async def add_pattern(zip_json, archi_payload: Optional[dict] = None):
    # Prepare working copy
    output_dir = Path("output_project")
    work = Path("old_project_work")
    process_payload(zip_json, work)

    # Load README and discover services
    # Read README (kept for context) and discover service folders
    readme = read_text_if_exists(work, "Readme.md")
    services = find_services(work)

    # Prefer Archi JSON payload when provided (in-memory). Otherwise fall back to README parsing.
    if archi_payload:
        archi_map = load_patterns_from_archi(archi_payload)
        print("Using in-memory Archi payload to derive patterns")
        readme_assignments = match_labels_to_folders(archi_map, [s.name for s in services]) if archi_map else {}
    else:
        # Optionally derive patterns from README (fallback to roles for non-matched)
        readme_patterns = parse_patterns_from_readme(readme)
        print("README patterns:", readme_patterns)
        readme_assignments = match_readme_to_folders(readme_patterns, [s.name for s in services]) if readme_patterns else {}
    roles: dict = {"defaults": {}, "services": {}}

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    copy_tree(work, output_dir)

    # Init LLM
    init_llm_from_env()

    # Optional: build a GitHub retriever for RAG if token provided
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        try:
            await build_github_retriever(github_token, owner="microservices-patterns", repo="ftgo-application", branch="master")
            print("GitHub retriever built and available as GITHUB_RETRIEVER")
        except Exception as e:
            print(f"Could not build GitHub retriever: {e}")

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


if __name__ == "__main__":
    # Create new event loop for async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        payload = loop.run_until_complete(add_pattern({"filename": "microservices_project.zip", "zip_base64": "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frWjdS4JhlI/PRv5BaOMLCvQ5sO99rhiBfNyrE7n/m91YJKo3r0/UEsDBBQAAAAIAC2CZFsAAAAAAgAAAAAAAABGAAAAYXV0aGVudGljYXRpb25fc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2F1dGhlbnRpY2F0aW9uL21vZGVsLwMAUEsDBBQAAAAIAC2CZFvQydFYaAAAAIUAAABdAAAAYXV0aGVudGljYXRpb25fc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2F1dGhlbnRpY2F0aW9uL21vZGVsL1JlZ2lzdHJhdGlvblJlc3VsdC5qYXZhTY3BCcMwDEXvnkITeAFvkU6gKMIVlS0TyRAo3b2m9JB/fO/BH0gvrAxkLfOFbShnnPHkHkIYYj03O1hLSmPuKgSk6A4bV/E4f8XGPjXgnWDtX+1mytjBJxG7l7t7xCm9Qlt8XZf0+QJQSwMEFAAAAAgALYJkWwAAAAACAAAAAAAAAEYAAABhdXRoZW50aWNhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYXV0aGVudGljYXRpb24vbW9kZWwvAwBQSwMEFAAAAAgALYJkW7xtdy1iAAAAfQAAAFcAAABhdXRoZW50aWNhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYXV0aGVudGljYXRpb24vbW9kZWwvTG9naW5SZXF1ZXN0LmphdmFly7ENhDAMQNE+U3iCLJAVroIJfMYKFkmcI44OCbE7Kej47dOvSBtGBtLs+cBcE3vstnIxITTR4rMunIJztX+TEFDC1uCjUcrEv87N4HQweny2XUoEzijjekMd+1/3JbjrBlBLAwQUAAAACAAtgmRbAAAAAAIAAAAAAAAARgAAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9tb2RlbC8DAFBLAwQUAAAACAAtgmRbzYJhIHEAAACeAAAAVgAAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9tb2RlbC9Mb2dpblJlc3VsdC5q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AAAAAAAAAEYAAAAAAAAAAAAQAP1BVQkAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9tb2RlbC9QSwECFAMUAAAACAAtgmRbKVC1z3wAAADjAAAAXgAAAAAAAAAAAAAAgAG7CQAAYXV0aGVudGljYXRpb25fc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2F1dGhlbnRpY2F0aW9uL21vZGVsL1JlZ2lzdHJhdGlvblJlcXVlc3QuamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAABGAAAAAAAAAAAAEAD9QbMKAABhdXRoZW50aWNhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYXV0aGVudGljYXRpb24vbW9kZWwvUEsBAhQDFAAAAAgALYJkW9DJ0VhoAAAAhQAAAF0AAAAAAAAAAAAAAIABGQsAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9tb2RlbC9SZWdpc3RyYXRpb25SZXN1bHQuamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAABGAAAAAAAAAAAAEAD9QfwLAABhdXRoZW50aWNhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYXV0aGVudGljYXRpb24vbW9kZWwvUEsBAhQDFAAAAAgALYJkW7xtdy1iAAAAfQAAAFcAAAAAAAAAAAAAAIABYgwAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9tb2RlbC9Mb2dpblJlcXVlc3QuamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAABGAAAAAAAAAAAAEAD9QTkNAABhdXRoZW50aWNhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYXV0aGVudGljYXRpb24vbW9kZWwvUEsBAhQDFAAAAAgALYJkW82CYSBxAAAAngAAAFYAAAAAAAAAAAAAAIABnw0AAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9tb2RlbC9Mb2dpblJlc3VsdC5qYXZhUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAAEYAAAAAAAAAAAAQAP1BhA4AAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9tb2RlbC9QSwECFAMUAAAACAAtgmRbaauX4V8AAABpAAAAWAAAAAAAAAAAAAAAgAHqDgAAYXV0aGVudGljYXRpb25fc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2F1dGhlbnRpY2F0aW9uL21vZGVsL0xvZ291dFJlcXVlc3QuamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAABGAAAAAAAAAAAAEAD9Qb8PAABhdXRoZW50aWNhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYXV0aGVudGljYXRpb24vbW9kZWwvUEsBAhQDFAAAAAgALYJkWwTqZi9lAAAAfwAAAFcAAAAAAAAAAAAAAIABJRAAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9tb2RlbC9Mb2dvdXRSZXN1bHQuamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAABGAAAAAAAAAAAAEAD9Qf8QAABhdXRoZW50aWNhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYXV0aGVudGljYXRpb24vbW9kZWwvUEsBAhQDFAAAAAgALYJkW/CzcHlgAAAAcQAAAGAAAAAAAAAAAAAAAIABZREAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9tb2RlbC9TZXNzaW9uUmVmcmVzaFJlcXVlc3QuamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAABGAAAAAAAAAAAAEAD9QUMSAABhdXRoZW50aWNhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYXV0aGVudGljYXRpb24vbW9kZWwvUEsBAhQDFAAAAAgALYJkWxfIUil1AAAAqgAAAF8AAAAAAAAAAAAAAIABqRIAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9tb2RlbC9TZXNzaW9uUmVmcmVzaFJlc3VsdC5qYXZhUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAAEgAAAAAAAAAAAAQAP1BmxMAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9hdXRoZW50aWNhdGlvbi9zZXJ2aWNlL1BLAQIUAxQAAAAIAC2CZFslBcLrTAEAAMIEAABYAAAAAAAAAAAAAACAAQMUAABhdXRoZW50aWNhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYXV0aGVudGljYXRpb24vc2VydmljZS9BdXRoU2VydmljZS5qYXZhUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAACoAAAAAAAAAAAAQAP1BxRUAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2Uvc3JjL21haW4vcmVzb3VyY2VzL1BLAQIUAxQAAAAIAC2CZFt8twLadQAAAMIAAABAAAAAAAAAAAAAAACAAQ8WAABhdXRoZW50aWNhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL3Jlc291cmNlcy9hcHBsaWNhdGlvbi5wcm9wZXJ0aWVzUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAABcAAAAAAAAAAAAQAP1B4hYAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2UvUEsBAhQDFAAAAAgALYJkW5O9HymAAAAAigAAACEAAAAAAAAAAAAAAIABGRcAAGF1dGhlbnRpY2F0aW9uX3NlcnZpY2UvRG9ja2VyZmlsZVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAAVAAAAAAAAAAAAEAD9QdgXAAB1c2VyX3Byb2ZpbGVfc2VydmljZS9QSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAAOwAAAAAAAAAAABAA/UENGAAAdXNlcl9wcm9maWxlX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS91c2VycHJvZmlsZS9QSwECFAMUAAAACAAtgmRbw4ARzbcAAABdAQAAXQAAAAAAAAAAAAAAgAFoGAAAdXNlcl9wcm9maWxlX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS91c2VycHJvZmlsZS9Vc2VyUHJvZmlsZVNlcnZpY2VBcHBsaWNhdGlvbi5qYXZhUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAAEYAAAAAAAAAAAAQAP1BmhkAAHVzZXJfcHJvZmlsZV9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvdXNlcnByb2ZpbGUvY29udHJvbGxlci9QSwECFAMUAAAACAAtgmRb0rx7eCQBAABRAgAAYAAAAAAAAAAAAAAAgAEAGgAAdXNlcl9wcm9maWxlX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS91c2VycHJvZmlsZS9jb250cm9sbGVyL1VzZXJQcm9maWxlQ29udHJvbGxlci5qYXZhUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAAEEAAAAAAAAAAAAQAP1BohsAAHVzZXJfcHJvZmlsZV9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvdXNlcnByb2ZpbGUvbW9kZWwvUEsBAhQDFAAAAAgALYJkW1lYckReAAAAjwAAAFEAAAAAAAAAAAAAAIABAxwAAHVzZXJfcHJvZmlsZV9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvdXNlcnByb2ZpbGUvbW9kZWwvVXNlclByb2ZpbGUuamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAAoAAAAAAAAAAAAEAD9QdAcAAB1c2VyX3Byb2ZpbGVfc2VydmljZS9zcmMvbWFpbi9yZXNvdXJjZXMvUEsBAhQDFAAAAAgALYJkWxIvfOV5AAAAyQAAAD4AAAAAAAAAAAAAAIABGB0AAHVzZXJfcHJvZmlsZV9zZXJ2aWNlL3NyYy9tYWluL3Jlc291cmNlcy9hcHBsaWNhdGlvbi5wcm9wZXJ0aWVzUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAABUAAAAAAAAAAAAQAP1B7R0AAHVzZXJfcHJvZmlsZV9zZXJ2aWNlL1BLAQIUAxQAAAAIAC2CZFtC638afQAAAIgAAAAfAAAAAAAAAAAAAACAASIeAAB1c2VyX3Byb2ZpbGVfc2VydmljZS9Eb2NrZXJmaWxlUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAAB0AAAAAAAAAAAAQAP1B3B4AAGFncmljdWx0dXJhbF9jb21wYW55X3NlcnZpY2UvUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAAD8AAAAAAAAAAAAQAP1BGR8AAGFncmljdWx0dXJhbF9jb21wYW55X3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9jb21wYW55L1BLAQIUAxQAAAAIAC2CZFv0F5qlrgAAAFEBAABdAAAAAAAAAAAAAACAAXgfAABhZ3JpY3VsdHVyYWxfY29tcGFueV9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvY29tcGFueS9Db21wYW55U2VydmljZUFwcGxpY2F0aW9uLmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAASgAAAAAAAAAAABAA/UGhIAAAYWdyaWN1bHR1cmFsX2NvbXBhbnlfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2NvbXBhbnkvY29udHJvbGxlci9QSwECFAMUAAAACAAtgmRbVaZr4uMBAAC7BAAAYAAAAAAAAAAAAAAAgAELIQAAYWdyaWN1bHR1cmFsX2NvbXBhbnlfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2NvbXBhbnkvY29udHJvbGxlci9Db21wYW55Q29udHJvbGxlci5qYXZhUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAAEUAAAAAAAAAAAAQAP1BbCMAAGFncmljdWx0dXJhbF9jb21wYW55X3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9jb21wYW55L21vZGVsL1BLAQIUAxQAAAAIAC2CZFsJHHv6pwAAAJ8BAABRAAAAAAAAAAAAAACAAdEjAABhZ3JpY3VsdHVyYWxfY29tcGFueV9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvY29tcGFueS9tb2RlbC9Db21wYW55LmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAARQAAAAAAAAAAABAA/UHnJAAAYWdyaWN1bHR1cmFsX2NvbXBhbnlfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2NvbXBhbnkvbW9kZWwvUEsBAhQDFAAAAAgALYJkW5uRhD9+AAAA0wAAAGQAAAAAAAAAAAAAAIABTCUAAGFncmljdWx0dXJhbF9jb21wYW55X3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9jb21wYW55L21vZGVsL0NvbXBhbnlSZWdpc3RyYXRpb25SZXF1ZXN0LmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAAMAAAAAAAAAAAABAA/UFMJgAAYWdyaWN1bHR1cmFsX2NvbXBhbnlfc2VydmljZS9zcmMvbWFpbi9yZXNvdXJjZXMvUEsBAhQDFAAAAAgALYJkWw1i1F94AAAAxQAAAEYAAAAAAAAAAAAAAIABnCYAAGFncmljdWx0dXJhbF9jb21wYW55X3NlcnZpY2Uvc3JjL21haW4vcmVzb3VyY2VzL2FwcGxpY2F0aW9uLnByb3BlcnRpZXNQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAAHQAAAAAAAAAAABAA/UF4JwAAYWdyaWN1bHR1cmFsX2NvbXBhbnlfc2VydmljZS9QSwECFAMUAAAACAAtgmRbhI29P4YAAACQAAAAJwAAAAAAAAAAAAAAgAG1JwAAYWdyaWN1bHR1cmFsX2NvbXBhbnlfc2VydmljZS9Eb2NrZXJmaWxlUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAABgAAAAAAAAAAAAQAP1BgCgAAHByb2R1Y3RfY2F0YWxvZ19zZXJ2aWNlL1BLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAABBAAAAAAAAAAAAEAD9QbgoAABwcm9kdWN0X2NhdGFsb2dfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL3Byb2R1Y3RjYXRhbG9nL1BLAQIUAxQAAAAIAC2CZFs8qr7TtAAAAGYBAABmAAAAAAAAAAAAAACAARkpAABwcm9kdWN0X2NhdGFsb2dfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL3Byb2R1Y3RjYXRhbG9nL1Byb2R1Y3RDYXRhbG9nU2VydmljZUFwcGxpY2F0aW9uLmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAATAAAAAAAAAAAABAA/UFRKgAAcHJvZHVjdF9jYXRhbG9nX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9wcm9kdWN0Y2F0YWxvZy9jb250cm9sbGVyL1BLAQIUAxQAAAAIAC2CZFvOS89qtwEAABgGAABpAAAAAAAAAAAAAACAAb0qAABwcm9kdWN0X2NhdGFsb2dfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL3Byb2R1Y3RjYXRhbG9nL2NvbnRyb2xsZXIvUHJvZHVjdENhdGFsb2dDb250cm9sbGVyLmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAARwAAAAAAAAAAABAA/UH7LAAAcHJvZHVjdF9jYXRhbG9nX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9wcm9kdWN0Y2F0YWxvZy9tb2RlbC9QSwECFAMUAAAACAAtgmRb7fQW46cAAACgAQAAUwAAAAAAAAAAAAAAgAFiLQAAcHJvZHVjdF9jYXRhbG9nX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9wcm9kdWN0Y2F0YWxvZy9tb2RlbC9Qcm9kdWN0LmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAAKwAAAAAAAAAAABAA/UF6LgAAcHJvZHVjdF9jYXRhbG9nX3NlcnZpY2Uvc3JjL21haW4vcmVzb3VyY2VzL1BLAQIUAxQAAAAIAC2CZFtvHlbAfAAAAMwAAABBAAAAAAAAAAAAAACAAcUuAABwcm9kdWN0X2NhdGFsb2dfc2VydmljZS9zcmMvbWFpbi9yZXNvdXJjZXMvYXBwbGljYXRpb24ucHJvcGVydGllc1BLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAAYAAAAAAAAAAAAEAD9QaAvAABwcm9kdWN0X2NhdGFsb2dfc2VydmljZS9QSwECFAMUAAAACAAtgmRbrWyxfoEAAACLAAAAIgAAAAAAAAAAAAAAgAHYLwAAcHJvZHVjdF9jYXRhbG9nX3NlcnZpY2UvRG9ja2VyZmlsZVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAANAAAAAAAAAAAAEAD9QZkwAABjYXJ0X3NlcnZpY2UvUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAACwAAAAAAAAAAAAQAP1BxjAAAGNhcnRfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2NhcnQvUEsBAhQDFAAAAAgALYJkW7AZz7ysAAAASAEAAEcAAAAAAAAAAAAAAIABEjEAAGNhcnRfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2NhcnQvQ2FydFNlcnZpY2VBcHBsaWNhdGlvbi5qYXZhUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAADcAAAAAAAAAAAAQAP1BIzIAAGNhcnRfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2NhcnQvY29udHJvbGxlci9QSwECFAMUAAAACAAtgmRb/eZZWnYBAADBAwAASgAAAAAAAAAAAAAAgAF6MgAAY2FydF9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvY2FydC9jb250cm9sbGVyL0NhcnRDb250cm9sbGVyLmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAAMgAAAAAAAAAAABAA/UFYNAAAY2FydF9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvY2FydC9tb2RlbC9QSwECFAMUAAAACAAtgmRbzPMB6W8AAACJAAAAOwAAAAAAAAAAAAAAgAGqNAAAY2FydF9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvY2FydC9tb2RlbC9DYXJ0LmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAAMgAAAAAAAAAAABAA/UFyNQAAY2FydF9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvY2FydC9tb2RlbC9QSwECFAMUAAAACAAtgmRbd5ySCVsAAABwAAAAPwAAAAAAAAAAAAAAgAHENQAAY2FydF9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvY2FydC9tb2RlbC9DYXJ0SXRlbS5qYXZhUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAADIAAAAAAAAAAAAQAP1BfDYAAGNhcnRfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2NhcnQvbW9kZWwvUEsBAhQDFAAAAAgALYJkW9ctF95qAAAAkgAAAEcAAAAAAAAAAAAAAIABzjYAAGNhcnRfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2NhcnQvbW9kZWwvQWRkVG9DYXJ0UmVxdWVzdC5qYXZhUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAADIAAAAAAAAAAAAQAP1BnTcAAGNhcnRfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2NhcnQvbW9kZWwvUEsBAhQDFAAAAAgALYJkW7ZwjC1kAAAAfgAAAEwAAAAAAAAAAAAAAIAB7zcAAGNhcnRfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2NhcnQvbW9kZWwvUmVtb3ZlRnJvbUNhcnRSZXF1ZXN0LmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAAIAAAAAAAAAAAABAA/UG9OAAAY2FydF9zZXJ2aWNlL3NyYy9tYWluL3Jlc291cmNlcy9QSwECFAMUAAAACAAtgmRbQwa2YHUAAADCAAAANgAAAAAAAAAAAAAAgAH9OAAAY2FydF9zZXJ2aWNlL3NyYy9tYWluL3Jlc291cmNlcy9hcHBsaWNhdGlvbi5wcm9wZXJ0aWVzUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAAA0AAAAAAAAAAAAQAP1BxjkAAGNhcnRfc2VydmljZS9QSwECFAMUAAAACAAtgmRb4Gdn1HYAAACAAAAAFwAAAAAAAAAAAAAAgAHzOQAAY2FydF9zZXJ2aWNlL0RvY2tlcmZpbGVQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAADgAAAAAAAAAAABAA/UGeOgAAb3JkZXJfc2VydmljZS9QSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAALgAAAAAAAAAAABAA/UHMOgAAb3JkZXJfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL29yZGVyL1BLAQIUAxQAAAAIAC2CZFsyVhXvrQAAAEsBAABKAAAAAAAAAAAAAACAARo7AABvcmRlcl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvb3JkZXIvT3JkZXJTZXJ2aWNlQXBwbGljYXRpb24uamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAA5AAAAAAAAAAAAEAD9QS88AABvcmRlcl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvb3JkZXIvY29udHJvbGxlci9QSwECFAMUAAAACAAtgmRbbe+QalYBAADPAgAATQAAAAAAAAAAAAAAgAGIPAAAb3JkZXJfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL29yZGVyL2NvbnRyb2xsZXIvT3JkZXJDb250cm9sbGVyLmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAANAAAAAAAAAAAABAA/UFJPgAAb3JkZXJfc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL29yZGVyL21vZGVsL1BLAQIUAxQAAAAIAC2CZFtyEHcjggAAAOMAAAA+AAAAAAAAAAAAAACAAZ0+AABvcmRlcl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvb3JkZXIvbW9kZWwvT3JkZXIuamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAA0AAAAAAAAAAAAEAD9QXs/AABvcmRlcl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvb3JkZXIvbW9kZWwvUEsBAhQDFAAAAAgALYJkW0Ck0o1dAAAAcgAAAEIAAAAAAAAAAAAAAIABzz8AAG9yZGVyX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9vcmRlci9tb2RlbC9PcmRlckl0ZW0uamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAA0AAAAAAAAAAAAEAD9QYxAAABvcmRlcl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvb3JkZXIvbW9kZWwvUEsBAhQDFAAAAAgALYJkWwedLWKCAAAAtQAAAEUAAAAAAAAAAAAAAIAB4EAAAG9yZGVyX3NlcnZpY2Uvc3JjL21haW4vamF2YS9jb20vZXhhbXBsZS9vcmRlci9tb2RlbC9PcmRlclJlcXVlc3QuamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAAhAAAAAAAAAAAAEAD9QcVBAABvcmRlcl9zZXJ2aWNlL3NyYy9tYWluL3Jlc291cmNlcy9QSwECFAMUAAAACAAtgmRb2YbISHYAAADDAAAANwAAAAAAAAAAAAAAgAEGQgAAb3JkZXJfc2VydmljZS9zcmMvbWFpbi9yZXNvdXJjZXMvYXBwbGljYXRpb24ucHJvcGVydGllc1BLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAAOAAAAAAAAAAAAEAD9QdFCAABvcmRlcl9zZXJ2aWNlL1BLAQIUAxQAAAAIAC2CZFtapklHdwAAAIEAAAAYAAAAAAAAAAAAAACAAf9CAABvcmRlcl9zZXJ2aWNlL0RvY2tlcmZpbGVQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAAFwAAAAAAAAAAABAA/UGsQwAAYWRtaW5pc3RyYXRpb25fc2VydmljZS9QSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAANwAAAAAAAAAAABAA/UHjQwAAYWRtaW5pc3RyYXRpb25fc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2FkbWluL1BLAQIUAxQAAAAIAC2CZFvlkJGFrQAAAF0BAABcAAAAAAAAAAAAAACAATpEAABhZG1pbmlzdHJhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYWRtaW4vQWRtaW5pc3RyYXRpb25TZXJ2aWNlQXBwbGljYXRpb24uamF2YVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAABCAAAAAAAAAAAAEAD9QWFFAABhZG1pbmlzdHJhdGlvbl9zZXJ2aWNlL3NyYy9tYWluL2phdmEvY29tL2V4YW1wbGUvYWRtaW4vY29udHJvbGxlci9QSwECFAMUAAAACAAtgmRbOHx7jQ4BAADIAQAAVgAAAAAAAAAAAAAAgAHDRQAAYWRtaW5pc3RyYXRpb25fc2VydmljZS9zcmMvbWFpbi9qYXZhL2NvbS9leGFtcGxlL2FkbWluL2NvbnRyb2xsZXIvQWRtaW5Db250cm9sbGVyLmphdmFQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAAKgAAAAAAAAAAABAA/UFFRwAAYWRtaW5pc3RyYXRpb25fc2VydmljZS9zcmMvbWFpbi9yZXNvdXJjZXMvUEsBAhQDFAAAAAgALYJkW+W8gcF2AAAAwwAAAEAAAAAAAAAAAAAAAIABj0cAAGFkbWluaXN0cmF0aW9uX3NlcnZpY2Uvc3JjL21haW4vcmVzb3VyY2VzL2FwcGxpY2F0aW9uLnByb3BlcnRpZXNQSwECFAMUAAAACAAtgmRbAAAAAAIAAAAAAAAAFwAAAAAAAAAAABAA/UFjSAAAYWRtaW5pc3RyYXRpb25fc2VydmljZS9QSwECFAMUAAAACAAtgmRbzkIMUH8AAACKAAAAIQAAAAAAAAAAAAAAgAGaSAAAYWRtaW5pc3RyYXRpb25fc2VydmljZS9Eb2NrZXJmaWxlUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAAAkAAAAAAAAAAAAQAP1BWEkAAGZyb250ZW5kL1BLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAAJAAAAAAAAAAAAEAD9QYFJAABmcm9udGVuZC9QSwECFAMUAAAACAAtgmRbuRKlZ2wAAABwAAAAEwAAAAAAAAAAAAAAgAGqSQAAZnJvbnRlbmQvRG9ja2VyZmlsZVBLAQIUAxQAAAAIAC2CZFsAAAAAAgAAAAAAAAAJAAAAAAAAAAAAEAD9QUdKAABmcm9udGVuZC9QSwECFAMUAAAACAAtgmRbXgryAIcAAADMAAAAFQAAAAAAAAAAAAAAgAFwSgAAZnJvbnRlbmQvcGFja2FnZS5qc29uUEsBAhQDFAAAAAgALYJkWwAAAAACAAAAAAAAAAkAAAAAAAAAAAAQAP1BKksAAGZyb250ZW5kL1BLAQIUAxQAAAAIAC2CZFswJqL7gwIAAEwJAAARAAAAAAAAAAAAAACAAVNLAABmcm9udGVuZC9pbmRleC5qc1BLBQYAAAAAcABwAPMsAAAFTgAAAAA="}))
    finally:
        loop.close()                                