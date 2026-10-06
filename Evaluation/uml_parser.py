import re


class UMLParser:
    def __init__(self):

        self.boundary_start_pattern = re.compile(
    r'(?i)^\s*(package|folder|frame|cloud|component|rectangle|database|interface|node)\s+'
    r'(?:\"[^\"]+\"|\[[^\]]+\])\s*(?:as\s+\w+)?[^{]*\{'
)
        self.boundary_end_pattern = re.compile(r'^\s*\}\s*$')
        

        # ========= Leaf Node Patterns =========
        self.leaf_patterns = {
            # Standard quoted formats
            "rectangle": re.compile(
                r'(?i)^\s*rectangle\s+"([^"]+)"'
                r'(?:\s+as\s+(\w+))?'
                r'(?:\s+<<([^>]+)>>)?\s*$'
            ),
            "database": re.compile(
                r'(?i)^\s*database\s+"([^"]+)"'
                r'(?:\s+as\s+(\w+))?'
                r'(?:\s+<<([^>]+)>>)?\s*$'
            ),
            "interface": re.compile(
                r'(?i)^\s*interface\s+"([^"]+)"'
                r'(?:\s+as\s+(\w+))?'
                r'(?:\s+<<([^>]+)>>)?\s*$'
            ),
            "node": re.compile(
                r'(?i)^\s*node\s+"([^"]+)"'
                r'(?:\s+as\s+(\w+))?'
                r'(?:\s+<<([^>]+)>>)?\s*$'
            ),
            "component": re.compile(
                r'(?i)^\s*component\s+'
                r'(?:\"([^\"]+)\"|\[([^\]]+)\])'
                r'(?:\s+as\s+(\w+))?'
                r'(?:\s+<<([^>]+)>>)?\s*$'
            ),
            "component_shorthand": re.compile(
                r'(?i)^\s*\[([^\]]+)\]'
                r'(?:\s+as\s+(\w+))?'
                r'(?:\s+<<([^>]+)>>)?\s*$'
            ),
            # Generator format: unquoted_identifier as "Quoted Name"
            "database_unquoted": re.compile(
                r'(?i)^\s*database\s+(\w+)\s+as\s+"([^"]+)"'
                r'(?:\s+<<([^>]+)>>)?\s*$'
            ),
            "component_unquoted": re.compile(
                r'(?i)^\s*component\s+(\w+)\s+as\s+"([^"]+)"'
                r'(?:\s+<<([^>]+)>>)?\s*$'
            ),
            # Reversed shorthand some generators (e.g. Kimi) emit:
            # [snake_case_alias] as "Readable Display Name" — the bracket
            # holds the alias, not the label. Without this, that line
            # matches neither component_shorthand (which requires an
            # unquoted \w+ alias after "as", not a quoted phrase) nor the
            # edge pattern (no --/-> in it), so it's silently skipped: the
            # service is never registered as an explicit leaf, only ever as
            # a same-named fallback node the first time an edge mentions it
            # — which then gets excluded as non-explicit by
            # canonicalize_for_ged, silently dropping the service AND every
            # edge touching it from the graph entirely.
            "component_shorthand_unquoted": re.compile(
                r'(?i)^\s*\[(\w+)\]\s+as\s+"([^"]+)"'
                r'(?:\s+<<([^>]+)>>)?\s*$'
            ),
            "component_bracket_unquoted": re.compile(
                r'(?i)^\s*component\s+\[(\w+)\]\s+as\s+"([^"]+)"'
                r'(?:\s+<<([^>]+)>>)?\s*$'
            ),
        }

        # Arrow alternatives, most specific first. The first three cover PlantUML's
        # single-dash forms ("<->", "->", "-down->", "-[#red]->", "<-"), which the
        # double-dash-only alternatives after them used to miss — silently
        # dropping every edge of diagrams written in that style.
        self.edge_pattern = re.compile(
            r'(?i)(.+?)\s*(?:'
            r'<-+(?:\[[^\]]*\])?-*>'
            r'|-+(?:\[[^\]]*\])?(?:up|down|left|right|u|d|l|r)?-*>'
            r'|<-+(?:\[[^\]]*\])?(?:up|down|left|right|u|d|l|r)?-*(?![->])'
            r'|--+(?:up|down|left|right)?-*>|\.\.+>|<--+>|<--+|\.\.-+|--+(?:up|down|left|right)?--+|(?<!\w)--+(?!\w)'
            r')\s*(.*)'
        )
        # Trailing colour/style tokens after a declaration's name/alias, e.g.
        # 'rectangle "Postman" as Postman #2EC7CC' or '... <<svc>> #line:red'.
        self.trailing_style_pattern = re.compile(r'(\s+#[\w#;:.\-]+)+\s*$')

    def parse(self, puml_code: str):
        nodes = set()
        explicit_nodes = set() 
        edges = []
        aliases = {}

        boundary_stack = []

        puml_code = re.sub(r"'.*$", "", puml_code, flags=re.MULTILINE)
        puml_code = re.sub(r"/'(.*?)'/", "", puml_code, flags=re.DOTALL)

        lines = puml_code.strip().split("\n")
        if not any("@startuml" in line for line in lines):
            return {"nodes": [], "edges": []}

        def full_name(name: str):
            prefix = "::".join(boundary_stack) if boundary_stack else "Global"
            return f"{prefix}::{name}"

        in_legend = False
        in_note = False
        for line in lines:
            line = line.strip()
            if not line or line.startswith("@") or "skinparam" in line:
                continue
            # Skip legend blocks
            if line.lower().startswith("legend"):
                in_legend = True
                continue
            if line.lower() == "endlegend":
                in_legend = False
                continue
            if in_legend:
                continue
            # Skip multi-line note blocks
            if re.match(r'(?i)^\s*note\s+(right|left|top|bottom|of)\b', line):
                # "note right of X : text" / "note right: text" is a complete
                # single-line note; only the colon-less form opens a block that
                # runs to "end note". Treating both as blocks swallowed every
                # line after the first inline note.
                if ":" not in line:
                    in_note = True
                continue
            if line.lower().strip() == "end note":
                in_note = False
                continue
            if in_note:
                continue
            # Skip title, !define, and table rows
            if line.startswith("!") or line.lower().startswith("title ") or line.startswith("|"):
                continue

            # ---------- boundary ----------
            if self.boundary_start_pattern.match(line):
                name = re.findall(r'\"([^\"]+)\"|\[([^\]]+)\]', line)
                if name:
                    pkg_name = name[0][0] or name[0][1]
                    fn = full_name(pkg_name)
                    nodes.add(fn)
                    aliases[pkg_name] = fn
                    aliases[f'"{pkg_name}"'] = fn
                    alias_m = re.search(r'\bas\s+(\w+)', line, re.IGNORECASE)
                    if alias_m:
                        aliases[alias_m.group(1)] = fn
                    boundary_stack.append(pkg_name)
                continue

            if self.boundary_end_pattern.match(line):
                if boundary_stack:
                    boundary_stack.pop()
                continue

            # ---------- leaf node ----------
            # Strip trailing colour tokens, but only after the last quote so a
            # "#" inside a quoted label is never touched.
            head, quote, tail = line.rpartition('"')
            decl = head + quote + self.trailing_style_pattern.sub("", tail) if quote else \
                self.trailing_style_pattern.sub("", line)
            matched_leaf = False
            for node_type, pattern in self.leaf_patterns.items():
                m = pattern.match(decl)
                if not m:
                    continue

                if node_type == "component":
                    name = m.group(1) or m.group(2)
                    alias = m.group(3)
                elif node_type == "component_shorthand":
                    name = m.group(1)
                    alias = m.group(2)
                elif node_type in (
                    "database_unquoted", "component_unquoted",
                    "component_shorthand_unquoted", "component_bracket_unquoted",
                ):
                    # For "database db_id as 'DB Name'" format (and the
                    # bracket-shorthand equivalents), use the quoted name (group 2)
                    name = m.group(2)
                    alias = m.group(1)  # The identifier is the alias
                else:
                    name, alias, _ = m.groups()

                fn = full_name(name)
                nodes.add(fn)
                explicit_nodes.add(fn)

                aliases[name] = fn
                aliases[f'"{name}"'] = fn
                aliases[f'[{name}]'] = fn
                if alias:
                    aliases[alias] = fn

                matched_leaf = True
                break

            if matched_leaf:
                continue

            # ---------- edge ----------
            edge_match = self.edge_pattern.search(line)
            if edge_match:
                src_raw = edge_match.group(1).split(":")[0].strip()
                dst_raw = edge_match.group(2).split(":")[0].strip()

                for raw in (src_raw, dst_raw):
                    if raw not in aliases:
                        clean = raw.strip(' "[]()')
                        fn = full_name(clean)
                        nodes.add(fn)
                        aliases[raw] = fn

                edges.append((src_raw, dst_raw))

        # ---------- resolve edges ----------
        resolved_edges = []
        strip_chars = ' "[]()'
        for s, d in edges:
            rs = aliases.get(s, f"Global::{s.strip(strip_chars)}")
            rd = aliases.get(d, f"Global::{d.strip(strip_chars)}")
            resolved_edges.append((rs, rd))

        def get_true_leaf_nodes(all_nodes_set, explicit_set):
            leaf_nodes_list = []
            for node in all_nodes_set:
                if node not in explicit_set:
                    continue
                parent_prefix = f"{node}::"
                is_parent = any(other.startswith(parent_prefix) for other in all_nodes_set)
                if not is_parent:
                    leaf_nodes_list.append(node)
            return leaf_nodes_list

        def get_service_nodes(all_nodes_set, explicit_set):
            """Top-level boundary nodes (Global::Name that have children)."""
            service_list = []
            for node in all_nodes_set:
                parts = node.split("::")
                if len(parts) == 2 and parts[0] == "Global":
                    child_prefix = f"{node}::"
                    has_children = any(other.startswith(child_prefix) for other in all_nodes_set)
                    if has_children:
                        service_list.append(node)
            # Fall back to all Global:: nodes (leaf services with no children)
            if not service_list:
                for node in all_nodes_set:
                    parts = node.split("::")
                    if len(parts) == 2 and parts[0] == "Global":
                        service_list.append(node)
            return service_list

        leaf_nodes = get_true_leaf_nodes(nodes, explicit_nodes)
        service_nodes = get_service_nodes(nodes, explicit_nodes)

        return {
            "nodes": list(nodes),
            "leafnodes": leaf_nodes,
            "servicenodes": service_nodes,
            "edges": resolved_edges
        }