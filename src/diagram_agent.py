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

    # Check @startuml / @enduml
    stripped = content.strip()
    if not stripped.startswith("@startuml"):
        issues.append("Missing `@startuml` at start of file")
    if not stripped.endswith("@enduml"):
        issues.append("Missing `@enduml` at end of file")

    # Check balanced curly braces
    open_braces = content.count("{")
    close_braces = content.count("}")
    if open_braces != close_braces:
        issues.append(
            f"Unbalanced curly braces: {open_braces} opening '{{' vs {close_braces} closing '}}'"
        )

    # Check balanced square brackets
    open_sq = content.count("[")
    close_sq = content.count("]")
    if open_sq != close_sq:
        issues.append(
            f"Unbalanced square brackets: {open_sq} opening '[' vs {close_sq} closing ']'"
        )

    # Check unclosed double-quotes per line
    for i, line in enumerate(lines, 1):
        # Skip comment lines
        if line.strip().startswith("'") or line.strip().startswith("/'"):
            continue
        quote_count = line.count('"')
        if quote_count % 2 != 0:
            issues.append(f"Line {i}: unclosed double-quote — `{line.strip()}`")

    # Check for empty file (only markers, no content)
    non_marker_lines = [
        l for l in lines
        if l.strip() and not l.strip().startswith("@")
    ]
    if len(non_marker_lines) == 0:
        issues.append("File is empty (no diagram content between @startuml and @enduml)")

    # Check for duplicate component/alias definitions
    # Patterns: [alias] as "Label", component "Label" as alias, database "name" as alias
    alias_defs: dict[str, list[int]] = {}
    component_pattern = re.compile(
        r'^\s*'
        r'(?:'
        r'\[(\w+)\]'                          # [alias]
        r'|(?:component|database|interface|actor|queue|node)\s+"[^"]*"\s+as\s+(\w+)'  # element "Label" as alias
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
                f"— each component must be defined once and referenced by alias elsewhere"
            )

    # Check for components defined inside multiple packages
    # Track which package each component definition lives in
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
        if len(pkgs) > 1:
            unique_pkgs = list(dict.fromkeys(pkgs))
            if len(unique_pkgs) > 1:
                issues.append(
                    f"Component `{alias}` appears in multiple packages: {', '.join(f'`{p}`' for p in unique_pkgs)} "
                    f"— define it once and use references elsewhere"
                )

    return issues


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
    # ------------------------------------------------------------------
    sandbox_extract = tempfile.mkdtemp(prefix=f"agent1_{prompt.title}_")
    shutil.copy2(
        os.path.join(dataset_dir, "input.txt"),
        os.path.join(sandbox_extract, "input.txt"),
    )
    print(f"--- SANDBOX: Agent 1 workspace → {sandbox_extract} (input.txt only) ---")

    extract_agent = Agent(
        llm=llm,
        tools=tools,
        visualize=DelegationVisualizer(name="Architecture Extractor"),
    )
    extract_conversation = Conversation(agent=extract_agent, workspace=sandbox_extract)
    extract_conversation.send_message(prompt.get_extract_prompt())

    start_time = time.time()
    extract_conversation.run()
    extract_time = time.time() - start_time
    extract_cost = (
        extract_conversation.conversation_stats.get_combined_metrics().accumulated_cost
    )

    # Copy output back
    arch_json_sandbox = os.path.join(sandbox_extract, "architecture.json")
    if os.path.exists(arch_json_sandbox):
        shutil.copy2(arch_json_sandbox, os.path.join(output_dir, "architecture.json"))
    else:
        print("--- WARNING: Agent 1 did not produce architecture.json ---")

    shutil.rmtree(sandbox_extract, ignore_errors=True)
    print(
        f"--- STEP_METRICS: Architecture Extraction"
        f" | Time: {extract_time:.2f}s | Cost: ${extract_cost:.4f} ---"
    )

    # ------------------------------------------------------------------
    # Agent 2 — Diagram Renderer (sandbox: only architecture.json)
    # ------------------------------------------------------------------
    sandbox_render = tempfile.mkdtemp(prefix=f"agent2_{prompt.title}_")
    arch_json_src = os.path.join(output_dir, "architecture.json")
    if os.path.exists(arch_json_src):
        shutil.copy2(arch_json_src, os.path.join(sandbox_render, "architecture.json"))
    print(f"--- SANDBOX: Agent 2 workspace → {sandbox_render} (architecture.json only) ---")

    render_agent = Agent(
        llm=llm,
        tools=tools,
        visualize=DelegationVisualizer(name="Diagram Renderer"),
    )
    render_conversation = Conversation(agent=render_agent, workspace=sandbox_render)
    render_conversation.send_message(prompt.get_render_prompt())

    start_time = time.time()
    render_conversation.run()
    render_time = time.time() - start_time
    render_cost = (
        render_conversation.conversation_stats.get_combined_metrics().accumulated_cost
    )

    # Copy outputs back
    for fname in ("component_diagram.puml", "architecture_summary.md"):
        src = os.path.join(sandbox_render, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(output_dir, fname))

    shutil.rmtree(sandbox_render, ignore_errors=True)
    print(
        f"--- STEP_METRICS: Diagram Rendering"
        f" | Time: {render_time:.2f}s | Cost: ${render_cost:.4f} ---"
    )

    # ------------------------------------------------------------------
    # Syntax Check — validate PlantUML and auto-correct if needed
    # ------------------------------------------------------------------
    syntax_fix_cost = 0.0
    syntax_fix_time = 0.0
    puml_path = os.path.join(output_dir, "component_diagram.puml")
    syntax_issues = validate_puml_syntax(puml_path)

    if syntax_issues:
        issues_text = "\n".join(f"- {issue}" for issue in syntax_issues)
        print(f"--- SYNTAX_CHECK: {len(syntax_issues)} issue(s) found. Running correction agent… ---")

        # Syntax fixer sandbox: only component_diagram.puml
        sandbox_fix = tempfile.mkdtemp(prefix=f"agent_fix_{prompt.title}_")
        shutil.copy2(puml_path, os.path.join(sandbox_fix, "component_diagram.puml"))

        fix_agent = Agent(
            llm=llm,
            tools=tools,
            visualize=DelegationVisualizer(name="Syntax Fixer"),
        )
        fix_conversation = Conversation(agent=fix_agent, workspace=sandbox_fix)
        fix_conversation.send_message(prompt.get_syntax_fix_prompt(issues_text))

        start_time = time.time()
        fix_conversation.run()
        syntax_fix_time = time.time() - start_time
        syntax_fix_cost = (
            fix_conversation.conversation_stats.get_combined_metrics().accumulated_cost
        )

        # Copy fixed file back
        fixed_puml = os.path.join(sandbox_fix, "component_diagram.puml")
        if os.path.exists(fixed_puml):
            shutil.copy2(fixed_puml, puml_path)

        shutil.rmtree(sandbox_fix, ignore_errors=True)

        # Verify fix worked
        remaining = validate_puml_syntax(puml_path)
        if remaining:
            print(f"--- SYNTAX_CHECK: ⚠️ {len(remaining)} issue(s) remain after fix attempt ---")
        else:
            print("--- SYNTAX_CHECK: ✅ All issues resolved ---")

        print(
            f"--- STEP_METRICS: Syntax Fix"
            f" | Time: {syntax_fix_time:.2f}s | Cost: ${syntax_fix_cost:.4f} ---"
        )
    else:
        print("--- SYNTAX_CHECK: ✅ No issues found ---")

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
