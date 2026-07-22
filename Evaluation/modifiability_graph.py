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
