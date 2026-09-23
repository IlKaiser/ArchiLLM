#!/usr/bin/env python3
"""One-off: render every modifiability scenario's component_diagram.puml to a
PNG via the public PlantUML server, same encoding run_headless.py already
uses for the main diagrams. Skips any .puml that already has a sibling .png.
"""
import sys
import time
import zlib
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def plantuml_encode(text: str) -> str:
    data = zlib.compress(text.encode("utf-8"))[2:-4]
    result = ""
    charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    for i in range(0, len(data), 3):
        b = data[i:i + 3]
        if len(b) == 1:
            b = b + bytes(2)
        elif len(b) == 2:
            b = b + bytes(1)
        n = (b[0] << 16) | (b[1] << 8) | b[2]
        result += (charset[(n >> 18) & 0x3F] + charset[(n >> 12) & 0x3F] +
                   charset[(n >> 6) & 0x3F] + charset[n & 0x3F])
    return result


def render(puml_path: Path) -> bool:
    png_path = puml_path.with_suffix(".png")
    if png_path.exists():
        return True
    try:
        encoded = plantuml_encode(puml_path.read_text(encoding="utf-8"))
        url = f"https://www.plantuml.com/plantuml/png/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ARCHILLMv2/1.0)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            png_path.write_bytes(resp.read())
        print(f"  ok  {puml_path.relative_to(REPO)}")
        return True
    except Exception as e:
        print(f"  FAIL {puml_path.relative_to(REPO)}: {e}")
        return False


def main():
    pumls = sorted((REPO / "results" / "student_projects").glob("*/modifiability/scenario_*/component_diagram.puml"))
    print(f"Found {len(pumls)} scenario diagrams")
    ok = fail = 0
    for p in pumls:
        if render(p):
            ok += 1
        else:
            fail += 1
        time.sleep(0.3)  # be polite to the public server
    print(f"\nDone: {ok} ok, {fail} failed")


if __name__ == "__main__":
    main()
