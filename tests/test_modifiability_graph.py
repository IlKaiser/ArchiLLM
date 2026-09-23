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


def test_canonicalize_drops_package_boundary_nodes():
    # "Global::Pkg" is a package/boundary node (it's in "nodes" but not
    # "leafnodes"); only the two services nested inside it are real
    # architectural elements.
    parsed = {
        "nodes": ["Global::Pkg", "Global::Pkg::Order Service", "Global::Pkg::Cart Service"],
        "leafnodes": ["Global::Pkg::Order Service", "Global::Pkg::Cart Service"],
        "edges": [("Global::Pkg::Order Service", "Global::Pkg::Cart Service")],
    }
    result = mg.canonicalize_for_ged(parsed)

    assert set(result["nodes"]) == {"Order Service", "Cart Service"}
    assert result["edges"] == [("Order Service", "Cart Service")]


def test_canonicalize_makes_package_rename_a_no_op_for_ged():
    # Renaming only the wrapping package's title must not change the GED
    # between two otherwise-identical diagrams — that's the whole point of
    # canonicalizing before computing graph edit distance.
    original = {
        "nodes": ["Global::Database per Service", "Global::Database per Service::Order Service"],
        "leafnodes": ["Global::Database per Service::Order Service"],
        "edges": [],
    }
    renamed = {
        "nodes": ["Global::Private Database per Service", "Global::Private Database per Service::Order Service"],
        "leafnodes": ["Global::Private Database per Service::Order Service"],
        "edges": [],
    }

    g1 = mg.build_graph(mg.canonicalize_for_ged(original))
    g2 = mg.build_graph(mg.canonicalize_for_ged(renamed))

    assert mg.compute_ged(g1, g2, timeout=5.0) == 0


def test_canonicalize_still_detects_a_real_added_service_under_a_renamed_package():
    # The mitigation must not mask genuine structural changes that happen to
    # arrive alongside a cosmetic package rename.
    original = {
        "nodes": ["Global::Database per Service", "Global::Database per Service::Order Service"],
        "leafnodes": ["Global::Database per Service::Order Service"],
        "edges": [],
    }
    renamed_plus_new_service = {
        "nodes": [
            "Global::Private Database per Service",
            "Global::Private Database per Service::Order Service",
            "Global::Private Database per Service::Loyalty Service",
        ],
        "leafnodes": [
            "Global::Private Database per Service::Order Service",
            "Global::Private Database per Service::Loyalty Service",
        ],
        "edges": [],
    }

    g1 = mg.build_graph(mg.canonicalize_for_ged(original))
    g2 = mg.build_graph(mg.canonicalize_for_ged(renamed_plus_new_service))

    ged = mg.compute_ged(g1, g2, timeout=5.0)
    assert ged == 1  # exactly one node insertion — the new service


def test_canonicalize_falls_back_to_all_nodes_when_leafnodes_missing():
    # Hand-built dicts without a "leafnodes" key (e.g. older callers, or the
    # simple fixtures in this file) must behave as a no-op, not drop
    # everything.
    parsed = {"nodes": ["Global::a", "Global::b"], "edges": [("Global::a", "Global::b")]}
    result = mg.canonicalize_for_ged(parsed)

    assert set(result["nodes"]) == {"a", "b"}
    assert result["edges"] == [("a", "b")]


def test_canonicalize_drops_edges_touching_a_package_node():
    parsed = {
        "nodes": ["Global::Pkg", "Global::Pkg::Order Service"],
        "leafnodes": ["Global::Pkg::Order Service"],
        "edges": [("Global::Pkg", "Global::Pkg::Order Service")],
    }
    result = mg.canonicalize_for_ged(parsed)

    assert result["edges"] == []


def test_normalize_ged_divides_by_baseline_node_plus_edge_count():
    # 3 nodes + 2 edges = baseline size 5.
    g = mg.build_graph({"nodes": ["a", "b", "c"], "edges": [("a", "b"), ("b", "c")]})
    assert mg.normalize_ged(10.0, g) == 2.0


def test_normalize_ged_same_raw_distance_scores_higher_on_a_smaller_baseline():
    small = mg.build_graph({"nodes": ["a", "b"], "edges": [("a", "b")]})  # size 3
    large = mg.build_graph({
        "nodes": ["a", "b", "c", "d", "e"],
        "edges": [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")],
    })  # size 9

    assert mg.normalize_ged(3.0, small) > mg.normalize_ged(3.0, large)


def test_normalize_ged_returns_none_for_none_ged():
    g = mg.build_graph({"nodes": ["a"], "edges": []})
    assert mg.normalize_ged(None, g) is None


def test_normalize_ged_returns_none_for_empty_baseline():
    empty = mg.build_graph({"nodes": [], "edges": []})
    assert mg.normalize_ged(4.0, empty) is None
