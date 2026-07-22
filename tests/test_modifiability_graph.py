import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Evaluation import modifiability_graph as mg


def test_build_graph_creates_nodes_and_edges():
    parsed = {"nodes": ["Global::a", "Global::b"], "edges": [("Global::a", "Global::b")]}
    graph = mg.build_graph(parsed)

    assert set(graph.nodes) == {"Global::a", "Global::b"}
    assert graph.nodes["Global::a"]["label"] == "Global::a"
    assert list(graph.edges) == [("Global::a", "Global::b")]


def test_compute_ged_zero_for_identical_graphs():
    parsed = {"nodes": ["Global::a", "Global::b"], "edges": [("Global::a", "Global::b")]}
    g1 = mg.build_graph(parsed)
    g2 = mg.build_graph(parsed)

    assert mg.compute_ged(g1, g2, timeout=5.0) == 0


def test_compute_ged_positive_for_extra_node():
    parsed1 = {"nodes": ["Global::a", "Global::b"], "edges": [("Global::a", "Global::b")]}
    parsed2 = {"nodes": ["Global::a", "Global::b", "Global::c"], "edges": [("Global::a", "Global::b")]}
    g1 = mg.build_graph(parsed1)
    g2 = mg.build_graph(parsed2)

    ged = mg.compute_ged(g1, g2, timeout=5.0)

    assert ged is not None
    assert ged > 0


def test_compute_ged_respects_node_identity_not_just_count():
    # Same number of nodes/edges, but different names -> nodes must not be
    # freely substitutable, or this would incorrectly return 0.
    parsed1 = {"nodes": ["Global::a", "Global::b"], "edges": [("Global::a", "Global::b")]}
    parsed2 = {"nodes": ["Global::x", "Global::y"], "edges": [("Global::x", "Global::y")]}
    g1 = mg.build_graph(parsed1)
    g2 = mg.build_graph(parsed2)

    ged = mg.compute_ged(g1, g2, timeout=5.0)

    assert ged is not None
    assert ged > 0
