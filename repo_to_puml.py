#!/usr/bin/env python3
"""
repo_to_puml.py
---------------
Given a list of GitHub repository URLs, fetches their structure and uses the
Claude API to generate a PlantUML component diagram for each one.

Usage
-----
    python repo_to_puml.py \
        https://github.com/microservices-patterns/ftgo-application \
        https://github.com/spring-projects/spring-petclinic

    # Or read repos from a file (one URL per line):
    python repo_to_puml.py --file repos.txt

    # Specify output directory:
    python repo_to_puml.py --out ./diagrams https://github.com/org/repo

Requirements
------------
    pip install anthropic requests

Environment
-----------
    ANTHROPIC_API_KEY  – your Anthropic API key (required)
    GITHUB_TOKEN       – optional, raises GitHub API rate limit from 60 to 5000 req/h
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
import anthropic
from dotenv import load_dotenv
load_dotenv()

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 8096
GITHUB_API = "https://api.github.com"
MAX_TREE_ENTRIES = 300   # cap tree size sent to Claude to stay within context

SYSTEM_PROMPT = """\
You are an expert software architect who specialises in reverse-engineering \
codebases and producing clear UML component diagrams in PlantUML format.

When given a repository's file tree, README, and any docker-compose / \
kubernetes manifests, you MUST output ONLY a valid PlantUML component diagram \
(starting with @startuml and ending with @enduml) with NO additional prose, \
markdown fences, or explanation.

Guidelines for the diagram:
- Use `component` blocks for each identifiable service or module.
- Use `database` blocks for persistence stores.
- Use `<<stereotype>>` annotations to classify components
  (e.g. <<service>>, <<gateway>>, <<broker>>, <<db>>, <<cache>>, <<client>>).
- Represent HTTP/REST relationships with solid arrows and a label.
- Represent async messaging (Kafka, RabbitMQ, SQS…) with dashed arrows and a label.
- Represent database access with solid arrows labelled with the protocol (JDBC, Redis, …).
- Nest sub-components (e.g. sagas, internal modules) inside their parent component.
- Add a skinparam block that colour-codes components by stereotype so the
  diagram is immediately readable.
- Keep it concise: omit test modules, build tooling, and CI configuration.
"""

INPUT_TXT_PROMPT = """\
You are an expert software architect analysing a software repository.
Your task is to produce a Product Requirements Document (PRD) in a specific structured format.

Output EXACTLY two sections, nothing else:

# SYSTEM DESCRIPTION:
<One paragraph (3-6 sentences) describing the system's purpose, its main functionality,
the type of users it serves, and any notable technical or product characteristics.
Do NOT use bullet points here — write a single cohesive paragraph.>

# USER STORIES:
<Numbered list of user stories in the format:
  N. As a <role>, I want <capability> so that <benefit>.
Each story should be on its own line, numbered starting from 1.
Aim for 20-40 stories covering all major features visible from the codebase.
Do NOT add any other text, headers, or commentary outside these two sections.>
"""

REQUIREMENTS_PROMPT = """\
You are an expert software architect who specializes in analyzing codebases and \
producing clear, structured requirements documents.

When given a repository's file tree, README, and configuration files, you MUST \
output a structured textual description of the application's requirements covering:

1. **Purpose**: What the application does, its main business goal
2. **Functional Requirements**: Key features and capabilities
3. **Non-Functional Requirements**: Performance, scalability, security considerations
4. **Architecture Patterns**: Microservices patterns used (if any), communication styles
5. **Tech Stack**: Primary languages, frameworks, databases, message brokers
6. **Deployment**: How the app is containerized/orchestrated (Docker, K8s, etc.)

Format the output as a clean, structured document with clear headings. \
Do NOT use markdown code fences. Output plain text with headers like "## Purpose" etc.
"""

# ──────────────────────────────────────────────
# GitHub helpers
# ──────────────────────────────────────────────

def _gh_headers() -> dict:
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def resolve_short_url(url: str) -> str:
    """Resolve shortened URLs (bit.ly, etc.) to final destination."""
    parsed = urlparse(url)
    # Check if it's a known shortener
    short_domains = ['bit.ly', 't.co', 'tinyurl.com', 'goo.gl', 'ow.ly', 'buff.ly']
    if parsed.netloc.lower() in short_domains or parsed.netloc.lower().endswith('.ly'):
        try:
            resp = requests.head(url, allow_redirects=True, timeout=30)
            resolved = resp.url
            print(f"  → Resolved {url} → {resolved}")
            return resolved
        except Exception as exc:
            print(f"  ⚠ Failed to resolve {url}: {exc}, using original")
            return url
    return url


def parse_github_url(url: str) -> tuple[str, str]:
    """Return (owner, repo) from a GitHub URL.
    
    Handles various GitHub URL formats including:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/branch/path
    - https://github.com/owner/repo/blob/branch/path/file
    """
    url = url.rstrip("/")
    # Match github.com/owner/repo followed by optional .git or /path
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?(?:/|$)", url)
    if not match:
        raise ValueError(f"Cannot parse GitHub URL: {url}")
    return match.group(1), match.group(2)


def fetch_repo_tree(owner: str, repo: str, branch: str = "HEAD") -> list[dict]:
    """Return the flat git tree for the default branch."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    resp = requests.get(url, headers=_gh_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("tree", [])


def fetch_file_content(owner: str, repo: str, path: str) -> Optional[str]:
    """Return raw text content of a file, or None on failure."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_gh_headers(), timeout=20)
    if resp.status_code != 200:
        return None
    import base64
    data = resp.json()
    if data.get("encoding") == "base64":
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            return None
    return data.get("content")


def collect_context(owner: str, repo: str) -> str:
    """
    Build a textual context string for Claude containing:
      1. The pruned file tree
      2. README (if present)
      3. docker-compose / kubernetes manifests (if present)
    """
    print(f"  → Fetching repository tree …")
    try:
        tree = fetch_repo_tree(owner, repo)
    except requests.HTTPError as exc:
        raise RuntimeError(f"GitHub API error fetching tree: {exc}") from exc

    # ── 1. File tree (pruned) ──────────────────
    interesting_extensions = {
        ".yaml", ".yml", ".json", ".toml", ".gradle", ".xml",
        ".tf", ".hcl", ".properties", ".env",
    }
    interesting_names = {
        "dockerfile", "docker-compose.yml", "docker-compose.yaml",
        "readme.md", "readme.rst", "readme.adoc", "readme.txt",
        "pom.xml", "build.gradle", "settings.gradle",
        "package.json", "requirements.txt", "pyproject.toml",
        "go.mod", "cargo.toml",
        "skaffold.yaml", "helmfile.yaml",
    }

    def is_interesting(entry: dict) -> bool:
        if entry["type"] != "blob":
            return False
        p = entry["path"].lower()
        name = Path(p).name
        ext = Path(p).suffix
        return (
            name in interesting_names
            or ext in interesting_extensions
            or "kubernetes" in p
            or "k8s" in p
            or "helm" in p
            or "deploy" in p
        )

    all_paths = [e["path"] for e in tree if e["type"] in ("blob", "tree")]
    interesting = [e for e in tree if is_interesting(e)]

    tree_lines = all_paths[:MAX_TREE_ENTRIES]
    if len(all_paths) > MAX_TREE_ENTRIES:
        tree_lines.append(f"… ({len(all_paths) - MAX_TREE_ENTRIES} more files truncated)")

    sections = [
        f"## Repository: {owner}/{repo}",
        "",
        "### File tree (abridged)",
        "```",
        *tree_lines,
        "```",
    ]

    # ── 2. README ──────────────────────────────
    readme_path = next(
        (e["path"] for e in tree
         if Path(e["path"]).name.lower().startswith("readme") and e["type"] == "blob"),
        None,
    )
    if readme_path:
        print(f"  → Fetching {readme_path} …")
        content = fetch_file_content(owner, repo, readme_path)
        if content:
            # Truncate very long READMEs
            if len(content) > 6000:
                content = content[:6000] + "\n… (truncated)"
            sections += ["", f"### {readme_path}", "```", content, "```"]

    # ── 3. docker-compose / k8s manifests ──────
    manifest_paths = [
        e["path"] for e in interesting
        if any(kw in e["path"].lower() for kw in
               ("docker-compose", "kubernetes", "k8s", "helm", "skaffold", "deploy"))
    ][:6]  # cap at 6 files

    for path in manifest_paths:
        print(f"  → Fetching {path} …")
        content = fetch_file_content(owner, repo, path)
        if content:
            if len(content) > 4000:
                content = content[:4000] + "\n… (truncated)"
            sections += ["", f"### {path}", "```yaml", content, "```"]

    return "\n".join(sections)


# ──────────────────────────────────────────────
# Claude helpers
# ──────────────────────────────────────────────

def generate_puml(context: str, client: anthropic.Anthropic) -> str:
    """Call Claude and return the raw PlantUML diagram string."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Analyse the repository context below and produce a PlantUML "
                    "component diagram. Output ONLY the PlantUML source, nothing else.\n\n"
                    + context
                ),
            }
        ],
    )
    raw = message.content[0].text.strip()

    # Strip accidental markdown fences if the model adds them
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\n?```$", "", raw)

    if not raw.startswith("@startuml"):
        raw = "@startuml\n" + raw
    if not raw.rstrip().endswith("@enduml"):
        raw = raw.rstrip() + "\n@enduml"

    return raw


def generate_requirements(context: str, client: anthropic.Anthropic) -> str:
    """Call Claude and return the textual requirements description."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=REQUIREMENTS_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Analyze the repository context below and produce a structured "
                    "requirements document. Output ONLY the requirements text, nothing else.\n\n"
                    + context
                ),
            }
        ],
    )
    raw = message.content[0].text.strip()
    return raw


def generate_input_txt(context: str, client: anthropic.Anthropic) -> str:
    """Call Claude and return an input.txt in the PRD format with SYSTEM DESCRIPTION + USER STORIES."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=INPUT_TXT_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Analyse the repository context below and produce the PRD document "
                    "with exactly the two sections specified. "
                    "Output ONLY the two sections, nothing else.\n\n"
                    + context
                ),
            }
        ],
    )
    raw = message.content[0].text.strip()
    # Ensure the two required headers are present; if the model forgot them, prepend a stub
    if "# SYSTEM DESCRIPTION:" not in raw:
        raw = "# SYSTEM DESCRIPTION:\n" + raw
    if "# USER STORIES:" not in raw:
        raw = raw + "\n\n# USER STORIES:\n"
    return raw


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def process_repo(
    url: str,
    base_dir: Path,
    client: anthropic.Anthropic,
    skip_existing: bool = True,
    gen_input_txt: bool = False,
    input_txt_only: bool = False,
) -> Optional[tuple[Path, Path, bool]]:
    """Process a single repository URL.

    Args:
        gen_input_txt:  also generate input.txt (PRD format: SYSTEM DESCRIPTION + USER STORIES).
        input_txt_only: generate ONLY input.txt, skip diagram and requirements.txt.

    Returns tuple of (puml_path, req_path, was_skipped).
    """
    print(f"\n{'─'*60}")
    print(f"Processing: {url}")

    # Resolve shortened URLs (bit.ly, etc.)
    resolved_url = resolve_short_url(url)

    owner, repo = parse_github_url(resolved_url)

    # Create subfolder for this repo under MicroserviceDataset
    repo_dir = base_dir / repo
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Check if already processed (has content)
    req_path = repo_dir / "requirements.txt"
    puml_path = repo_dir / "diagram.puml"
    input_txt_path = repo_dir / "input.txt"

    # Determine which files are expected
    if input_txt_only:
        expected = [input_txt_path]
    elif gen_input_txt:
        expected = [puml_path, req_path, input_txt_path]
    else:
        expected = [puml_path, req_path]

    if skip_existing and all(p.exists() for p in expected):
        print(f"  ⚡ Skipping — already exists: {repo_dir}")
        return (puml_path, req_path, True)

    # If folder exists but is incomplete, remove stale files
    if repo_dir.exists() and not all(p.exists() for p in expected):
        print(f"  🗑 Re-creating incomplete folder: {repo_dir}")
        for f in repo_dir.iterdir():
            f.unlink()

    try:
        context = collect_context(owner, repo)
    except Exception as exc:
        print(f"  ✗ Failed to fetch repo context: {exc}")
        return None

    if not input_txt_only:
        # Generate PlantUML diagram
        print(f"  → Generating PlantUML diagram via Claude ({MODEL}) …")
        try:
            puml = generate_puml(context, client)
            puml_path.write_text(puml, encoding="utf-8")
            print(f"  ✓ Written diagram → {puml_path}")
        except Exception as exc:
            print(f"  ✗ Failed to generate diagram: {exc}")
            return None

        # Generate requirements description
        print(f"  → Generating requirements description via Claude ({MODEL}) …")
        try:
            requirements = generate_requirements(context, client)
            req_path.write_text(requirements, encoding="utf-8")
            print(f"  ✓ Written requirements → {req_path}")
        except Exception as exc:
            print(f"  ✗ Failed to generate requirements: {exc}")
            return None

    if gen_input_txt or input_txt_only:
        # Generate input.txt in PRD format (SYSTEM DESCRIPTION + USER STORIES)
        print(f"  → Generating input.txt (PRD format) via Claude ({MODEL}) …")
        try:
            input_content = generate_input_txt(context, client)
            input_txt_path.write_text(input_content, encoding="utf-8")
            print(f"  ✓ Written input.txt → {input_txt_path}")
        except Exception as exc:
            print(f"  ✗ Failed to generate input.txt: {exc}")
            if input_txt_only:
                return None

    return (puml_path, req_path, False)  # False = was not skipped


def main():
    parser = argparse.ArgumentParser(
        description="Generate PlantUML component diagrams from GitHub repos using Claude."
    )
    parser.add_argument(
        "repos",
        nargs="*",
        metavar="REPO_URL",
        help="One or more GitHub repository URLs.",
    )
    parser.add_argument(
        "--file", "-f",
        metavar="FILE",
        help="Path to a text file with one GitHub URL per line.",
    )
    parser.add_argument(
        "--out", "-o",
        metavar="DIR",
        default="./MicroserviceDataset",
        help="Output directory for dataset (default: ./MicroserviceDataset).",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip repos that already have generated files (default: True).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if files exist (overrides --skip-existing).",
    )
    parser.add_argument(
        "--input-txt",
        action="store_true",
        help="Also generate input.txt in PRD format (# SYSTEM DESCRIPTION + # USER STORIES).",
    )
    parser.add_argument(
        "--input-txt-only",
        action="store_true",
        help="Generate ONLY input.txt (skip diagram and requirements.txt).",
    )
    args = parser.parse_args()

    # Collect URLs
    urls: list[str] = list(args.repos)
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        for line in file_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)

    if not urls:
        parser.print_help()
        sys.exit(1)

    # Validate API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # Prepare output directory
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    client = anthropic.Anthropic(api_key=api_key)

    # Determine skip behavior: skip existing unless --force is set
    skip_existing = args.skip_existing and not args.force
    
    if skip_existing:
        print("\n⚡ Skip mode: existing complete folders will be skipped (use --force to override)")
    
    results = []
    gen_input_txt = args.input_txt or args.input_txt_only
    input_txt_only = args.input_txt_only

    for i, url in enumerate(urls):
        try:
            result = process_repo(
                url, out_dir, client,
                skip_existing=skip_existing,
                gen_input_txt=gen_input_txt,
                input_txt_only=input_txt_only,
            )
            if result is None:
                results.append({"url": url, "status": "error", "error": "Processing failed"})
            else:
                puml_path, req_path, was_skipped = result
                results.append({
                    "url": url,
                    "status": "ok",
                    "puml": str(puml_path),
                    "requirements": str(req_path),
                    "skipped": was_skipped
                })
        except Exception as exc:
            print(f"  ✗ Failed: {exc}", file=sys.stderr)
            results.append({"url": url, "status": "error", "error": str(exc)})

        # Polite pause between repos to avoid hammering both APIs
        if i < len(urls) - 1:
            time.sleep(1)

    # Summary
    print(f"\n{'═'*60}")
    print("Summary")
    print(f"{'═'*60}")
    ok = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r.get("skipped", False)]
    fail = [r for r in results if r["status"] == "error"]
    print(f"  Succeeded : {len(ok)}")
    print(f"  Skipped   : {len(skipped)}")
    print(f"  Failed    : {len(fail)}")
    for r in fail:
        print(f"    ✗ {r['url']} — {r['error']}")
    if ok:
        print(f"\nDataset written to: {out_dir.resolve()}")
        print(f"  Structure: {out_dir.name}/<repo_name>/diagram.puml")
        print(f"             {out_dir.name}/<repo_name>/requirements.txt")


if __name__ == "__main__":
    main()
