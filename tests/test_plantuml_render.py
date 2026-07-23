import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import plantuml_render


def test_plantuml_encode_is_deterministic_and_nonempty():
    text = "@startuml\n[order_service]\n@enduml"
    encoded1 = plantuml_render.plantuml_encode(text)
    encoded2 = plantuml_render.plantuml_encode(text)

    assert encoded1 != ""
    assert encoded1 == encoded2


def test_plantuml_encode_differs_for_different_input():
    a = plantuml_render.plantuml_encode("@startuml\n[a]\n@enduml")
    b = plantuml_render.plantuml_encode("@startuml\n[a]\n[b]\n@enduml")
    assert a != b


def test_plantuml_image_url_embeds_encoded_text():
    text = "@startuml\n[order_service]\n@enduml"
    url = plantuml_render.plantuml_image_url(text)
    assert url == f"https://www.plantuml.com/plantuml/png/{plantuml_render.plantuml_encode(text)}"
    assert url.startswith("https://www.plantuml.com/plantuml/png/")
