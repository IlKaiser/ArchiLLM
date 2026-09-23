import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Evaluation.uml_parser import UMLParser


def test_component_shorthand_name_then_alias():
    puml = '@startuml\n[Order Service] as order_service\n@enduml'
    parsed = UMLParser().parse(puml)
    assert any("Order Service" in n for n in parsed["nodes"])


def test_component_shorthand_reversed_alias_then_quoted_name():
    # Some generators (Kimi observed in practice) emit the alias inside the
    # brackets and the human-readable label after "as", in quotes — the
    # opposite convention from component_shorthand's usual
    # "[Display Name] as alias". Without support for this, the line matched
    # neither a leaf pattern nor the edge pattern and was silently dropped,
    # so the service was never an explicit leaf node.
    puml = '@startuml\n[order_service] as "Order Service"\n@enduml'
    parsed = UMLParser().parse(puml)
    assert len(parsed["leafnodes"]) == 1
    assert any("Order Service" in n for n in parsed["leafnodes"])


def test_component_keyword_bracket_reversed_alias_then_quoted_name():
    puml = '@startuml\ncomponent [order_service] as "Order Service"\n@enduml'
    parsed = UMLParser().parse(puml)
    assert len(parsed["leafnodes"]) == 1
    assert any("Order Service" in n for n in parsed["leafnodes"])


def test_reversed_shorthand_edges_survive_leaf_filtering():
    # The real-world symptom: with the bug, this service+database pair
    # parsed as 0 "true" leaves (only edge-fallback nodes), so
    # canonicalize_for_ged dropped every edge touching them. Confirm the
    # fixed parser registers both ends as explicit leaves and keeps the
    # edge between them.
    puml = (
        '@startuml\n'
        '[order_service] as "Order Service"\n'
        'database "orders_db" as orders_db\n'
        'order_service -- orders_db\n'
        '@enduml'
    )
    parsed = UMLParser().parse(puml)
    assert len(parsed["leafnodes"]) == 2
    assert len(parsed["edges"]) == 1


def test_mixed_shorthand_conventions_in_the_same_file():
    # A file using the standard convention for one component and the
    # reversed one for another must parse both correctly, independently.
    puml = (
        '@startuml\n'
        '[Cart Service] as cart_service\n'
        '[order_service] as "Order Service"\n'
        'cart_service --> order_service : REST\n'
        '@enduml'
    )
    parsed = UMLParser().parse(puml)
    assert len(parsed["leafnodes"]) == 2
    assert len(parsed["edges"]) == 1


def test_database_unquoted_still_works():
    puml = '@startuml\ndatabase orders_db as "Orders Database"\n@enduml'
    parsed = UMLParser().parse(puml)
    assert len(parsed["leafnodes"]) == 1
    assert any("Orders Database" in n for n in parsed["leafnodes"])


def test_no_startuml_returns_empty():
    assert UMLParser().parse("just some text") == {"nodes": [], "edges": []}
