import os
import re
import shutil
import tempfile
import time

from openhands.sdk import (
    LLM,
    Agent,
    Conversation,
    Tool,
)
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool
from openhands.tools.apply_patch import ApplyPatchTool
from openhands.tools.delegate import (
    DelegateTool,
    DelegationVisualizer,
)
from openhands.sdk.context.condenser import LLMSummarizingCondenser

from src.prompt import DiagramPrompt
from src.effort_router import EffortRouter

from dotenv import load_dotenv
load_dotenv()


def validate_puml_syntax(filepath: str) -> list[str]:
    """Check PlantUML file for common syntax issues. Returns list of error descriptions."""
    issues = []
    if not os.path.exists(filepath):
        return ["File does not exist"]

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()

    # ── 1. @startuml / @enduml wrappers ────────────────────────────────────
    stripped = content.strip()
    if not stripped.startswith("@startuml"):
        issues.append("Missing `@startuml` at start of file")
    if not stripped.endswith("@enduml"):
        issues.append("Missing `@enduml` at end of file")

    # ── 2. Balanced curly braces ────────────────────────────────────────────
    open_braces = content.count("{")
    close_braces = content.count("}")
    if open_braces != close_braces:
        issues.append(
            f"Unbalanced curly braces: {open_braces} opening '{{' vs {close_braces} closing '}}'"
        )

    # ── 3. Balanced square brackets ─────────────────────────────────────────
    open_sq = content.count("[")
    close_sq = content.count("]")
    if open_sq != close_sq:
        issues.append(
            f"Unbalanced square brackets: {open_sq} opening '[' vs {close_sq} closing ']'"
        )

    # ── 4. Unclosed double-quotes per line ──────────────────────────────────
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("'") or line.strip().startswith("/'"):
            continue
        if line.count('"') % 2 != 0:
            issues.append(f"Line {i}: unclosed double-quote — `{line.strip()}`")

    # ── 5. Empty file ────────────────────────────────────────────────────────
    non_marker_lines = [
        l for l in lines
        if l.strip() and not l.strip().startswith("@")
    ]
    if len(non_marker_lines) == 0:
        issues.append("File is empty (no diagram content between @startuml and @enduml)")

    # ── 6. Invalid labeled-arrow syntax: A -- LABEL --> B ───────────────────
    # PlantUML does not support inline labels between two dashes like this.
    # Correct form: A --> B : label
    labeled_arrow_pat = re.compile(
        r'^\s*\S.*\s--\s+\w[\w\s]*\s+--[>.]'
    )
    for i, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if stripped_line.startswith("'") or stripped_line.startswith("/'") or stripped_line.startswith("/*"):
            continue
        if labeled_arrow_pat.match(line):
            issues.append(
                f"Line {i}: invalid arrow syntax `{stripped_line}` — "
                f"use `A --> B : label` instead of `A -- LABEL --> B`"
            )

    # ── 7. Arrows inside component/database/package blocks ──────────────────
    # `-->`, `..>`, `->` inside a `{ }` block are invalid
    arrow_pat = re.compile(r'(?:-->|\.\.>|->|--\s)')
    brace_depth = 0
    for i, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if stripped_line.startswith("'") or stripped_line.startswith("/'"):
            continue
        brace_depth += line.count("{") - line.count("}")
        if brace_depth > 0 and arrow_pat.search(stripped_line):
            # Allow lines that are themselves the opening of a block
            if not stripped_line.endswith("{"):
                issues.append(
                    f"Line {i}: arrow inside a block (depth {brace_depth}) — `{stripped_line}` — "
                    f"move relationships outside all `{{ }}` blocks"
                )

    # ── 8. Unclosed legend / note / header / footer blocks ──────────────────
    block_keywords = {
        "legend": "endlegend",
        "note": "end note",
        "header": "endheader",
        "footer": "endfooter",
    }
    for kw, end_kw in block_keywords.items():
        open_count = sum(
            1 for l in lines
            if re.match(rf'^\s*{kw}\b', l.strip(), re.IGNORECASE)
               and not l.strip().lower().startswith(f"end{kw}")
               and not l.strip().lower().startswith(f"end {kw}")
        )
        close_count = sum(
            1 for l in lines
            if re.match(rf'^\s*{end_kw}\b', l.strip(), re.IGNORECASE)
        )
        if open_count != close_count:
            issues.append(
                f"Unclosed `{kw}` block: {open_count} opening(s) vs {close_count} `{end_kw}` closing(s)"
            )

    # ── 9. Unquoted package/frame names containing hyphens or spaces ─────────
    unquoted_pkg_pat = re.compile(
        r'^\s*(?:package|frame|rectangle)\s+([^\s"{][^\s"{]*[-\s][^\s"{]*)\s*(?:\{|$)'
    )
    for i, line in enumerate(lines, 1):
        m = unquoted_pkg_pat.match(line)
        if m:
            issues.append(
                f"Line {i}: package/frame name `{m.group(1)}` contains hyphens or spaces — "
                f'wrap it in double quotes: `"{m.group(1)}"`'
            )

    # ── 10. Bare diagram-type keyword on its own line (e.g. "ComponentDiagram") ──
    invalid_kw_pat = re.compile(
        r'^\s*(ComponentDiagram|SequenceDiagram|ClassDiagram|UseCaseDiagram|ActivityDiagram|StateDiagram)\s*$',
        re.IGNORECASE,
    )
    for i, line in enumerate(lines, 1):
        if invalid_kw_pat.match(line):
            issues.append(
                f"Line {i}: `{line.strip()}` is not valid PlantUML — remove this line "
                f"(component diagrams only need `@startuml`)"
            )

    # ── 10b. Trailing garbage after @enduml ─────────────────────────────────
    for i, line in enumerate(lines, 1):
        if re.match(r'^\s*@enduml.+', line.strip()):
            issues.append(
                f"Line {i}: `{line.strip()}` — `@enduml` must be on its own line with no trailing characters"
            )

    # ── 10c. C-style block comments /* ... */ — not valid in PlantUML ────────
    if re.search(r'/\*', content):
        issues.append(
            "C-style `/* */` comments are not valid PlantUML — "
            "use `' single-line` or `/' block '/` comments instead"
        )

    # ── 11. Stray bare words / filenames on their own line ──────────────────
    # A line that is just a bare word with no PlantUML keyword or arrow is likely
    # a stray filename the model accidentally emitted (e.g. "component_diagram.puml")
    stray_line_pat = re.compile(r'^\s*[\w.-]+\.(puml|wsd|json|txt|md)\s*$', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        if stray_line_pat.match(line):
            issues.append(
                f"Line {i}: stray filename `{line.strip()}` — remove this line"
            )

    # ── 12. Duplicate alias definitions ─────────────────────────────────────
    alias_defs: dict[str, list[int]] = {}
    component_pattern = re.compile(
        r'^\s*'
        r'(?:'
        r'\[(\w+)\]'
        r'|(?:component|database|interface|actor|queue|node)\s+"[^"]*"\s+as\s+(\w+)'
        r')'
    )
    for i, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if stripped_line.startswith("'") or stripped_line.startswith("/'"):
            continue
        m = component_pattern.match(line)
        if m:
            alias = m.group(1) or m.group(2)
            if alias:
                alias_defs.setdefault(alias, []).append(i)

    for alias, line_nums in alias_defs.items():
        if len(line_nums) > 1:
            issues.append(
                f"Duplicate definition of `{alias}` on lines {', '.join(str(n) for n in line_nums)} "
                f"— each component must be defined once"
            )

    # ── 13. Components defined in multiple packages ──────────────────────────
    current_package = None
    pkg_depth = 0
    component_packages: dict[str, list[str]] = {}
    pkg_pattern = re.compile(r'^\s*(?:package|frame|rectangle|node)\s+"([^"]*)"')

    for line in lines:
        stripped_line = line.strip()
        pkg_m = pkg_pattern.match(line)
        if pkg_m:
            current_package = pkg_m.group(1)
            pkg_depth += 1
        elif stripped_line == "}" and pkg_depth > 0:
            pkg_depth -= 1
            if pkg_depth == 0:
                current_package = None
        if current_package:
            comp_m = component_pattern.match(line)
            if comp_m:
                alias = comp_m.group(1) or comp_m.group(2)
                if alias:
                    component_packages.setdefault(alias, []).append(current_package)

    for alias, pkgs in component_packages.items():
        unique_pkgs = list(dict.fromkeys(pkgs))
        if len(unique_pkgs) > 1:
            issues.append(
                f"Component `{alias}` appears in multiple packages: {', '.join(f'`{p}`' for p in unique_pkgs)} "
                f"— define it once and use references elsewhere"
            )

    return issues


def _generate_fallback_puml(arch_json_path: str, output_path: str) -> None:
    """Generate a minimal but syntactically valid PlantUML diagram from architecture.json.

    Used when Agent 2 fails all retries and produces no file at all.
    Does NOT call any LLM — pure Python.
    """
    import json

    if not os.path.exists(arch_json_path):
        print("--- FALLBACK_PUML: ⚠️ architecture.json not found — cannot generate fallback ---")
        return

    try:
        with open(arch_json_path, "r", encoding="utf-8") as f:
            arch = json.load(f)
    except Exception as e:
        print(f"--- FALLBACK_PUML: ⚠️ Failed to parse architecture.json: {e} ---")
        return

    services = arch.get("microservices", arch.get("services", []))
    patterns = arch.get("patterns", [])
    datastores = arch.get("datastores", [])
    dependencies = arch.get("dependencies", [])

    def alias(name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_]", "_", name).lower()

    lines = ["@startuml", "skinparam componentStyle rectangle", ""]

    # Group services by pattern
    pattern_map: dict[str, list[str]] = {}
    service_aliases: dict[str, str] = {}
    for svc in services:
        name = svc.get("name", "unknown")
        a = alias(name)
        service_aliases[name] = a
        # find which pattern this service belongs to
        svc_pattern = None
        for pat in patterns:
            involved = pat.get("services", pat.get("involved_services", []))
            if name in involved:
                svc_pattern = pat.get("name", pat.get("pattern", "uncategorized"))
                break
        svc_pattern = svc_pattern or "uncategorized"
        pattern_map.setdefault(svc_pattern, []).append(name)

    # Emit packages
    for pat_name, svc_names in pattern_map.items():
        lines.append(f'package "{pat_name}" {{')
        for svc_name in svc_names:
            a = service_aliases[svc_name]
            lines.append(f'  component "{svc_name}" as {a}')
            # Attach datastores that belong to this service
            for ds in datastores:
                owner = ds.get("owner", ds.get("service", ds.get("owning_service", "")))
                if owner == svc_name:
                    ds_name = ds.get("name", "db")
                    ds_alias = alias(ds_name)
                    lines.append(f'  database "{ds_name}" as {ds_alias}')
                    lines.append(f"  {a} -- {ds_alias}")
        lines.append("}")
        lines.append("")

    # Emit inter-service dependencies
    for dep in dependencies:
        src_name = dep.get("from", "")
        dst_name = dep.get("to", "")
        protocol = dep.get("protocol", "REST")
        src_a = service_aliases.get(src_name, alias(src_name))
        dst_a = service_aliases.get(dst_name, alias(dst_name))
        if src_a and dst_a:
            lines.append(f"{src_a} --> {dst_a} : {protocol}")

    lines += [
        "",
        "legend",
        "  Arrow label = protocol (REST / event / gRPC / WebSocket)",
        "  database = datastore owned by adjacent component",
        "endlegend",
        "",
        "@enduml",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"--- FALLBACK_PUML: ✅ Generated fallback diagram at {output_path} ---")


def _deterministic_puml_repair(filepath: str) -> None:
    """Best-effort deterministic repair of common PlantUML syntax issues.

    Applied only when all LLM fixer retries are exhausted.  Modifies the file
    in-place.  Does NOT rewrite the architecture — only structural syntax.
    """
    if not os.path.exists(filepath):
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Strip accidental markdown fences
    content = re.sub(r"^```[a-z]*\n?", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\n?```\s*$", "", content)

    # 2. Convert C-style /* */ comments to PlantUML ' comments (single-pass, handles multiline)
    content = re.sub(
        r'/\*.*?\*/',
        lambda m: "' " + " ".join(m.group(0)[2:-2].split()),
        content,
        flags=re.DOTALL,
    )

    stripped = content.strip()

    # 3. Ensure @startuml / @enduml wrappers
    if not stripped.startswith("@startuml"):
        stripped = "@startuml\n" + stripped
    if not stripped.rstrip().endswith("@enduml"):
        stripped = stripped.rstrip() + "\n@enduml"

    lines = stripped.splitlines()

    # 4. Remove stray bare filenames and invalid bare diagram-type keywords
    stray_pat = re.compile(r'^\s*[\w.-]+\.(puml|wsd|json|txt|md)\s*$', re.IGNORECASE)
    invalid_kw_pat = re.compile(
        r'^\s*(ComponentDiagram|SequenceDiagram|ClassDiagram|UseCaseDiagram|ActivityDiagram|StateDiagram)\s*$',
        re.IGNORECASE,
    )
    lines = [l for l in lines if not stray_pat.match(l) and not invalid_kw_pat.match(l)]

    # 4b. Strip trailing garbage after @enduml (e.g. "@enduml>")
    lines = [
        re.sub(r'^(\s*@enduml).*$', r'\1', l) if re.match(r'^\s*@enduml.+', l) else l
        for l in lines
    ]

    # 5. Fix invalid A -- LABEL --> B arrow syntax → A --> B : LABEL
    labeled_arrow_fix = re.compile(
        r'^(\s*)(\S+.*?)\s+--\s+(\w[\w\s]*?)\s+-->\s+(\S+.*?)\s*$'
    )
    lines = [
        labeled_arrow_fix.sub(r'\1\2 --> \4 : \3', l)
        if not l.strip().startswith("'") else l
        for l in lines
    ]

    # 6. Fix unquoted package/frame names with hyphens or spaces
    unquoted_pkg_fix = re.compile(
        r'^(\s*(?:package|frame|rectangle))\s+([^\s"{][^\s"{]*[-\s][^\s"{]*)\s*(\{?)$'
    )
    lines = [
        unquoted_pkg_fix.sub(lambda m: f'{m.group(1)} "{m.group(2)}" {m.group(3)}'.rstrip(), l)
        for l in lines
    ]

    result_lines = []
    open_braces = 0

    for line in lines:
        stripped_line = line.strip()
        # 6. Fix unclosed double-quotes on non-comment lines
        if not stripped_line.startswith("'") and not stripped_line.startswith("/'"):
            if line.count('"') % 2 != 0:
                line = line.rstrip() + '"'
        # 7. Remove arrows that are still inside { } blocks
        open_braces += line.count("{") - line.count("}")
        if open_braces > 0 and not stripped_line.endswith("{"):
            arrow_in_block = re.compile(r'(?:-->|\.\.>|->)')
            if arrow_in_block.search(stripped_line) and not stripped_line.startswith("'"):
                result_lines.append(f"' [moved-out] {stripped_line}")
                continue
        result_lines.append(line)

    # 8. Close any unclosed { blocks before @enduml
    open_braces = sum(l.count("{") - l.count("}") for l in result_lines)
    if open_braces > 0:
        enduml_idx = None
        for i in range(len(result_lines) - 1, -1, -1):
            if result_lines[i].strip() == "@enduml":
                enduml_idx = i
                break
        insert_at = enduml_idx if enduml_idx is not None else len(result_lines)
        for _ in range(open_braces):
            result_lines.insert(insert_at, "}")

    # 9. Close unclosed legend blocks
    legend_opens = sum(
        1 for l in result_lines
        if re.match(r'^\s*legend\b', l, re.IGNORECASE)
           and not re.match(r'^\s*endlegend\b', l, re.IGNORECASE)
    )
    legend_closes = sum(1 for l in result_lines if re.match(r'^\s*endlegend\b', l, re.IGNORECASE))
    if legend_opens > legend_closes:
        enduml_idx = next(
            (i for i in range(len(result_lines) - 1, -1, -1) if result_lines[i].strip() == "@enduml"),
            len(result_lines)
        )
        for _ in range(legend_opens - legend_closes):
            result_lines.insert(enduml_idx, "endlegend")

    # 10. Remove duplicate alias definitions — keep only the first occurrence
    alias_pattern = re.compile(
        r'^\s*'
        r'(?:'
        r'\[(\w+)\]'
        r'|(?:component|database|interface|actor|queue|node)\s+"[^"]*"\s+as\s+(\w+)'
        r')'
    )
    seen_aliases: set[str] = set()
    deduped_lines = []
    for line in result_lines:
        m = alias_pattern.match(line)
        if m:
            alias = m.group(1) or m.group(2)
            if alias:
                if alias in seen_aliases:
                    deduped_lines.append(f"' [dedup-removed] {line.rstrip()}")
                    continue
                seen_aliases.add(alias)
        deduped_lines.append(line)

    repaired = "\n".join(deduped_lines)

    # 11. Balance square brackets at whole-file level (last resort)
    open_sq = repaired.count("[")
    close_sq = repaired.count("]")
    if open_sq != close_sq:
        diff = open_sq - close_sq
        if 0 < diff <= 5:
            repaired = repaired.rstrip().rstrip("@enduml").rstrip() + ("\n]" * diff) + "\n@enduml"
        elif diff < 0 and abs(diff) <= 5:
            for _ in range(abs(diff)):
                repaired = re.sub(r'\n\s*\]\s*(?=\n)', "", repaired, count=1)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(repaired)


def run(
    prompt: DiagramPrompt,
    use_multi_agent: bool = False,
    use_validator: bool = False,
    local_llm_config: dict | None = None,
) -> float:
    """
    Two-agent pipeline for UML component diagram generation.

    Agent 1 — Architecture Extractor:
        Reads dataset/student_projects/{title}/ input files, extracts the
        microservices architecture (services, patterns, datastores,
        dependencies) and saves it as run/{title}/architecture.json.

    Agent 2 — Diagram Renderer:
        Reads run/{title}/architecture.json and produces:
          - run/{title}/component_diagram.puml  (PlantUML component diagram)
          - run/{title}/architecture_summary.md (Markdown summary tables)

    No implementation code is generated at any stage.

    Args:
        local_llm_config: if provided (from src.local_llm.get_local_llm_config),
            overrides LLM_MODEL / LLM_API_KEY / LLM_BASE_URL for the primary LLM.
            The secondary LLM (multi-agent) still uses SECONDARY_LLM_* env vars
            unless those are also overridden via environment.
    """
    # Resolve primary LLM params — local config wins over env vars
    if local_llm_config:
        primary_model   = local_llm_config["model"]
        primary_api_key = local_llm_config["api_key"]
        primary_url     = local_llm_config["base_url"]
        # Local models typically don't support native streaming tool-calling
        native_tools    = False
        temperature     = 0.7
        top_p           = 0.95
        print(f"--- LOCAL LLM: {primary_model} @ {primary_url} ---")
    else:
        primary_model   = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
        primary_api_key = os.getenv("LLM_API_KEY")
        primary_url     = os.getenv("LLM_BASE_URL", None)
        native_tools    = True
        temperature     = 1.0
        top_p           = 0.95

    condenser_llm = LLM(
        model=primary_model,
        api_key=primary_api_key,
        base_url=primary_url,
        top_p=top_p,
        native_tool_calling=native_tools,
    )

    llm = LLM(
        model=primary_model,
        condenser=LLMSummarizingCondenser(
            llm=condenser_llm,
            max_size=50,
            keep_first=20,
        ),
        api_key=primary_api_key,
        base_url=primary_url,
        temperature=temperature,
        top_p=top_p,
        native_tool_calling=native_tools,
        usage_id="diagram-agent",
    )

    secondary_llm = LLM(
        usage_id="diagram-agent-secondary",
        model=os.getenv("SECONDARY_LLM_MODEL", "openhands/devstral-medium-2507"),
        base_url=os.getenv("LLM_BASE_URL", None),
        api_key=os.getenv("SECONDARY_LLM_API_KEY"),
        condenser=LLMSummarizingCondenser(
            llm=LLM(
                model=os.getenv("SECONDARY_LLM_MODEL"),
                base_url=os.getenv("LLM_BASE_URL", None),
                api_key=os.getenv("SECONDARY_LLM_API_KEY"),
                top_p=0.95,
                native_tool_calling=False,
            ),
            max_size=50,
            keep_first=20,
        ),
        top_p=0.95,
        native_tool_calling=False,
    )

    if use_multi_agent:
        llm = EffortRouter(
            usage_id="effort-router",
            llms_for_routing={"primary": llm, "secondary": secondary_llm},
        )

    tools = [
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
        Tool(name=TerminalTool.name),
        Tool(name=ApplyPatchTool.name),
        Tool(name=DelegateTool.name),
    ]

    cwd = os.getcwd()
    output_dir = os.path.join(cwd, "run", prompt.title)
    os.makedirs(output_dir, exist_ok=True)

    dataset_dir = os.path.join(cwd, "dataset", "student_projects", prompt.title)

    # ------------------------------------------------------------------
    # Agent 1 — Architecture Extractor (sandbox: only input.txt)
    #           Retried up to MAX_EXTRACT_RETRIES times if no output produced
    # ------------------------------------------------------------------
    MAX_EXTRACT_RETRIES = 3
    extract_time = 0.0
    extract_cost = 0.0
    arch_json_output = os.path.join(output_dir, "architecture.json")

    for extract_attempt in range(1, MAX_EXTRACT_RETRIES + 1):
        sandbox_extract = tempfile.mkdtemp(prefix=f"agent1_{prompt.title}_")
        shutil.copy2(
            os.path.join(dataset_dir, "input.txt"),
            os.path.join(sandbox_extract, "input.txt"),
        )
        print(
            f"--- SANDBOX: Agent 1 workspace → {sandbox_extract} "
            f"(attempt {extract_attempt}/{MAX_EXTRACT_RETRIES}) ---"
        )

        extract_agent = Agent(
            llm=llm,
            tools=tools,
            visualize=DelegationVisualizer(name=f"Architecture Extractor (attempt {extract_attempt})"),
        )
        extract_conversation = Conversation(agent=extract_agent, workspace=sandbox_extract)
        extract_conversation.send_message(prompt.get_extract_prompt(workspace_dir=sandbox_extract))

        start_time = time.time()
        extract_conversation.run()
        extract_time += time.time() - start_time
        extract_cost += (
            extract_conversation.conversation_stats.get_combined_metrics().accumulated_cost
        )

        arch_json_sandbox = os.path.join(sandbox_extract, "architecture.json")
        if os.path.exists(arch_json_sandbox):
            shutil.copy2(arch_json_sandbox, arch_json_output)
            shutil.rmtree(sandbox_extract, ignore_errors=True)
            print(f"--- AGENT1: ✅ architecture.json produced on attempt {extract_attempt} ---")
            break

        shutil.rmtree(sandbox_extract, ignore_errors=True)
        print(f"--- AGENT1: ⚠️ architecture.json not produced on attempt {extract_attempt} ---")
    else:
        print(
            f"--- AGENT1: ❌ architecture.json not produced after {MAX_EXTRACT_RETRIES} attempts. "
            f"Aborting pipeline. ---"
        )
        print(
            f"--- STEP_METRICS: Architecture Extraction"
            f" | Time: {extract_time:.2f}s | Cost: ${extract_cost:.4f} ---"
        )
        return extract_cost + 0.0  # surface cost; run_pipeline handles missing output

    print(
        f"--- STEP_METRICS: Architecture Extraction"
        f" | Time: {extract_time:.2f}s | Cost: ${extract_cost:.4f} ---"
    )

    # ------------------------------------------------------------------
    # Agent 2 — Diagram Renderer (sandbox: only architecture.json)
    #           Retried up to MAX_RENDER_RETRIES if component_diagram.puml missing
    # ------------------------------------------------------------------
    MAX_RENDER_RETRIES = 3
    render_time = 0.0
    render_cost = 0.0
    arch_json_src = os.path.join(output_dir, "architecture.json")

    for render_attempt in range(1, MAX_RENDER_RETRIES + 1):
        sandbox_render = tempfile.mkdtemp(prefix=f"agent2_{prompt.title}_")
        if os.path.exists(arch_json_src):
            shutil.copy2(arch_json_src, os.path.join(sandbox_render, "architecture.json"))
        print(
            f"--- SANDBOX: Agent 2 workspace → {sandbox_render} "
            f"(attempt {render_attempt}/{MAX_RENDER_RETRIES}) ---"
        )

        render_agent = Agent(
            llm=llm,
            tools=tools,
            visualize=DelegationVisualizer(name=f"Diagram Renderer (attempt {render_attempt})"),
        )
        render_conversation = Conversation(agent=render_agent, workspace=sandbox_render)
        render_conversation.send_message(prompt.get_render_prompt(workspace_dir=sandbox_render))

        start_time = time.time()
        render_conversation.run()
        render_time += time.time() - start_time
        render_cost += (
            render_conversation.conversation_stats.get_combined_metrics().accumulated_cost
        )

        puml_sandbox = os.path.join(sandbox_render, "component_diagram.puml")
        if os.path.exists(puml_sandbox):
            for fname in ("component_diagram.puml", "architecture_summary.md"):
                src = os.path.join(sandbox_render, fname)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(output_dir, fname))
            shutil.rmtree(sandbox_render, ignore_errors=True)
            print(f"--- AGENT2: ✅ component_diagram.puml produced on attempt {render_attempt} ---")
            break

        # Fallback: scan sandbox for any .puml file the model wrote under a wrong name
        puml_candidates = [
            f for f in os.listdir(sandbox_render)
            if f.endswith(".puml") or f.endswith(".wsd")
        ]
        if puml_candidates:
            src = os.path.join(sandbox_render, puml_candidates[0])
            shutil.copy2(src, os.path.join(output_dir, "component_diagram.puml"))
            print(
                f"--- AGENT2: ⚠️ component_diagram.puml not found but rescued "
                f"`{puml_candidates[0]}` on attempt {render_attempt} ---"
            )
            shutil.rmtree(sandbox_render, ignore_errors=True)
            break

        shutil.rmtree(sandbox_render, ignore_errors=True)
        print(f"--- AGENT2: ⚠️ component_diagram.puml not produced on attempt {render_attempt} ---")
    else:
        print(
            f"--- AGENT2: ❌ component_diagram.puml not produced after {MAX_RENDER_RETRIES} attempts. ---"
        )
        # Last resort: generate a minimal valid PUML directly from architecture.json
        _generate_fallback_puml(arch_json_src, os.path.join(output_dir, "component_diagram.puml"))

    print(
        f"--- STEP_METRICS: Diagram Rendering"
        f" | Time: {render_time:.2f}s | Cost: ${render_cost:.4f} ---"
    )

    # ------------------------------------------------------------------
    # Syntax Check — validate and retry until clean (max MAX_SYNTAX_RETRIES)
    # ------------------------------------------------------------------
    MAX_SYNTAX_RETRIES = 3
    syntax_fix_cost = 0.0
    syntax_fix_time = 0.0
    puml_path = os.path.join(output_dir, "component_diagram.puml")

    if not os.path.exists(puml_path):
        print("--- SYNTAX_CHECK: ⚠️ component_diagram.puml not produced by render agent — skipping ---")
        syntax_issues = []
    else:
        syntax_issues = validate_puml_syntax(puml_path)

    if not syntax_issues:
        if os.path.exists(puml_path):
            print("--- SYNTAX_CHECK: ✅ No issues found ---")
    else:
        for attempt in range(1, MAX_SYNTAX_RETRIES + 1):
            issues_text = "\n".join(f"- {issue}" for issue in syntax_issues)
            print(
                f"--- SYNTAX_CHECK: {len(syntax_issues)} issue(s) found "
                f"(attempt {attempt}/{MAX_SYNTAX_RETRIES}). Running correction agent… ---"
            )

            sandbox_fix = tempfile.mkdtemp(prefix=f"agent_fix_{prompt.title}_")
            shutil.copy2(puml_path, os.path.join(sandbox_fix, "component_diagram.puml"))

            fix_agent = Agent(
                llm=llm,
                tools=tools,
                visualize=DelegationVisualizer(name=f"Syntax Fixer (attempt {attempt})"),
            )
            fix_conversation = Conversation(agent=fix_agent, workspace=sandbox_fix)
            fix_conversation.send_message(prompt.get_syntax_fix_prompt(issues_text, workspace_dir=sandbox_fix))

            start_time = time.time()
            fix_conversation.run()
            syntax_fix_time += time.time() - start_time
            syntax_fix_cost += (
                fix_conversation.conversation_stats.get_combined_metrics().accumulated_cost
            )

            fixed_puml = os.path.join(sandbox_fix, "component_diagram.puml")
            if os.path.exists(fixed_puml):
                shutil.copy2(fixed_puml, puml_path)

            shutil.rmtree(sandbox_fix, ignore_errors=True)

            syntax_issues = validate_puml_syntax(puml_path)
            if not syntax_issues:
                print(f"--- SYNTAX_CHECK: ✅ All issues resolved on attempt {attempt} ---")
                break

            print(
                f"--- SYNTAX_CHECK: ⚠️ {len(syntax_issues)} issue(s) remain after attempt {attempt} ---"
            )
        else:
            # All LLM attempts exhausted — apply deterministic fallback repair
            print(
                f"--- SYNTAX_CHECK: 🔧 LLM retries exhausted. Applying deterministic fallback repair… ---"
            )
            _deterministic_puml_repair(puml_path)
            syntax_issues = validate_puml_syntax(puml_path)
            if not syntax_issues:
                print("--- SYNTAX_CHECK: ✅ Deterministic repair succeeded ---")
            else:
                remaining_text = "; ".join(syntax_issues)
                print(
                    f"--- SYNTAX_CHECK: ❌ {len(syntax_issues)} issue(s) remain after fallback: "
                    f"{remaining_text} ---"
                )

        print(
            f"--- STEP_METRICS: Syntax Fix"
            f" | Time: {syntax_fix_time:.2f}s | Cost: ${syntax_fix_cost:.4f} ---"
        )

    # ------------------------------------------------------------------
    # Agent 3 — Validator (optional, needs dataset + run outputs)
    # ------------------------------------------------------------------
    validate_cost = 0.0
    validate_time = 0.0
    if use_validator:
        validate_agent = Agent(
            llm=llm,
            tools=tools,
            visualize=DelegationVisualizer(name="Validator"),
        )
        validate_conversation = Conversation(agent=validate_agent, workspace=cwd)
        validate_conversation.send_message(prompt.get_validate_prompt())

        start_time = time.time()
        validate_conversation.run()
        validate_time = time.time() - start_time
        validate_cost = (
            validate_conversation.conversation_stats.get_combined_metrics().accumulated_cost
        )
        print(
            f"--- STEP_METRICS: Validation"
            f" | Time: {validate_time:.2f}s | Cost: ${validate_cost:.4f} ---"
        )

    final_cost = extract_cost + render_cost + syntax_fix_cost + validate_cost
    final_time = extract_time + render_time + syntax_fix_time + validate_time
    print(
        f"--- FINAL_METRICS: Total Time: {final_time:.2f}s"
        f" | Total Cost: ${final_cost:.4f} ---"
    )
    return final_cost


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run UML component diagram pipeline.")
    parser.add_argument(
        "--title",
        required=True,
        help="Project title matching a folder under dataset/student_projects/",
    )
    parser.add_argument(
        "--multi-agent",
        action="store_true",
        help="Enable EffortRouter multi-agent delegation",
    )
    args = parser.parse_args()

    diagram_prompt = DiagramPrompt(title=args.title)
    run(prompt=diagram_prompt, use_multi_agent=args.multi_agent)
