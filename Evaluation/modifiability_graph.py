"""
modifiability_graph.py — build networkx graphs from parsed PlantUML
diagrams (via Evaluation.uml_parser.UMLParser) and compute the real graph
edit distance between two architecture versions.
"""
from __future__ import annotations

import networkx as nx


def build_graph(parsed: dict) -> nx.DiGraph:
    """Build a directed graph from a UMLParser.parse() result
    ({"nodes": [...], "edges": [(src, dst), ...], ...}).
    Each node carries a "label" attribute equal to its name, so node_match
    in compute_ged can compare nodes by identity rather than treating all
    nodes as freely substitutable.
    """
    graph = nx.DiGraph()
    for node in parsed["nodes"]:
        graph.add_node(node, label=node)
    for src, dst in parsed["edges"]:
        graph.add_edge(src, dst)
    return graph


def canonicalize_for_ged(parsed: dict) -> dict:
    """Reduce a UMLParser.parse() result to the nodes/edges that represent
    real architectural elements — services and datastores — for
    graph-edit-distance comparison.

    UMLParser identifies every node by its full nested-package path (e.g.
    "Global::Database per Service (mandatory for every microservice)::Event
    Sourcing (Ingredient Storage Event Log)::Ingredient Storage Service"),
    because `package { ... }` blocks are themselves added to the graph as
    boundary nodes and every node inside one is namespaced under its title.
    A package box is a rendering grouping (which pattern a service is drawn
    under), not an architectural element with a "logical role" of its own —
    but because it's namespaced, rewording its title alone (e.g. "Database
    per Service" -> "Private Database per Service") changes the identity of
    every component nested inside it, and graph_edit_distance then treats
    the whole subtree as deleted-and-reinserted even though nothing about
    the actual services/datastores/edges changed.

    This drops package/boundary nodes entirely (they carry no distinguishing
    edges of their own) and renames each surviving leaf node from its full
    path down to just its own declared name — the last "::" segment — so
    two diagrams are only scored as different where their real components or
    dependency edges actually differ, not where a purely cosmetic package
    title changed. Falls back to using all of `nodes` as leaves when
    `leafnodes` isn't present (e.g. hand-built dicts in tests), so it's a
    no-op mitigation on inputs that were already flat.
    """
    leaves = set(parsed.get("leafnodes") or parsed.get("nodes", []))

    def local_name(full_path: str) -> str:
        return full_path.rsplit("::", 1)[-1]

    nodes = [local_name(n) for n in leaves]
    edges = [
        (local_name(s), local_name(d))
        for s, d in parsed.get("edges", [])
        if s in leaves and d in leaves
    ]
    return {"nodes": nodes, "edges": edges}


def normalize_ged(ged: float | None, g_original: nx.DiGraph) -> float | None:
    """Scale a raw graph edit distance by the baseline graph's own size
    (its node count + edge count), so a fixed number of edits counts for
    less against a large architecture than against a small one — a GED of 6
    against an 11-node, 13-edge baseline (SmartCuisine) is a much bigger
    proportional change than a GED of 6 against a 28-node, 42-edge one
    (EFarmers). Returns None when ged itself is None (inconclusive/timed
    out) or the baseline graph is empty (nothing to normalize against).
    """
    if ged is None:
        return None
    baseline_size = g_original.number_of_nodes() + g_original.number_of_edges()
    if baseline_size == 0:
        return None
    return ged / baseline_size


def compute_ged(g1: nx.DiGraph, g2: nx.DiGraph, timeout: float = 10.0) -> float | None:
    """Real (exact) graph edit distance via networkx, bounded by timeout.
    Returns None if no result was found within the timeout — callers should
    treat this as inconclusive, not as a zero distance.
    """
    return nx.graph_edit_distance(
        g1, g2,
        node_match=lambda a, b: a.get("label") == b.get("label"),
        timeout=timeout,
    )
