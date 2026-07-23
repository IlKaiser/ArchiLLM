"""
plantuml_render.py — encodes PlantUML text into a plantuml.com PNG image URL.

Self-contained (deflate + the PlantUML-specific base64-like alphabet); does
not import or depend on app.py, so this module can be reused without
touching app.py's existing diagram-pipeline code (which has its own copy of
the same small algorithm).
"""
from __future__ import annotations

import zlib


def _encode6bit(b: int) -> str:
    if b < 10:
        return chr(48 + b)
    b -= 10
    if b < 26:
        return chr(65 + b)
    b -= 26
    if b < 26:
        return chr(97 + b)
    b -= 26
    return '-' if b == 0 else '_'


def _append3bytes(b1: int, b2: int, b3: int) -> str:
    return (
        _encode6bit((b1 >> 2) & 0x3F)
        + _encode6bit(((b1 & 0x3) << 4 | b2 >> 4) & 0x3F)
        + _encode6bit(((b2 & 0xF) << 2 | b3 >> 6) & 0x3F)
        + _encode6bit(b3 & 0x3F)
    )


def plantuml_encode(text: str) -> str:
    data = zlib.compress(text.encode("utf-8"))[2:-4]
    result = ""
    for i in range(0, len(data), 3):
        chunk = data[i : i + 3]
        b1, b2, b3 = chunk[0], chunk[1] if len(chunk) > 1 else 0, chunk[2] if len(chunk) > 2 else 0
        result += _append3bytes(b1, b2, b3)
    return result


def plantuml_image_url(puml_text: str) -> str:
    return f"https://www.plantuml.com/plantuml/png/{plantuml_encode(puml_text)}"
