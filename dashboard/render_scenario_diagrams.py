#!/usr/bin/env python3
"""One-off: render every missing component_diagram.puml (baseline and
modifiability-scenario alike) under a results/ tree to a PNG via the public
PlantUML server, same encoding run_headless.py already uses for the main
diagrams. Skips any .puml that already has a sibling .png.

Usage: python dashboard/render_scenario_diagrams.py [results/some_model/dataset]
Defaults to results/student_projects (the original DeepSeek run) for
backward compat.
"""
import subprocess
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


def _fetch(url: str, png_path: Path) -> None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ARCHILLMv2/1.0)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            png_path.write_bytes(resp.read())
    except Exception:
        # Some PlantUML CDN edges reject long encoded URLs from urllib while
        # accepting the identical URL through curl (same fallback
        # run_headless.py's render_puml_to_png already relies on).
        subprocess.run(["curl", "-fsSL", url, "-o", str(png_path)], check=True, timeout=30)


def render(puml_path: Path, attempts: int = 3) -> bool:
    png_path = puml_path.with_suffix(".png")
    if png_path.exists():
        return True
    encoded = plantuml_encode(puml_path.read_text(encoding="utf-8"))
    url = f"https://www.plantuml.com/plantuml/png/{encoded}"
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            _fetch(url, png_path)
            suffix = f" (attempt {attempt})" if attempt > 1 else ""
            print(f"  ok  {puml_path.relative_to(REPO)}{suffix}")
            return True
        except Exception as e:
            last_exc = e
            # The public server intermittently 400s on valid input under
            # repeated automated requests — a short backoff and retry
            # resolves it more often than not, confirmed by manually
            # re-fetching a "failed" URL seconds later and getting a real PNG.
            if attempt < attempts:
                time.sleep(3 * attempt)
    print(f"  FAIL {puml_path.relative_to(REPO)}: {last_exc}")
    return False


def main():
    root_rel = sys.argv[1] if len(sys.argv) > 1 else "results/student_projects"
    root = REPO / root_rel
    pumls = sorted(root.glob("*/component_diagram.puml")) + \
        sorted(root.glob("*/modifiability/scenario_*/component_diagram.puml"))
    print(f"Found {len(pumls)} diagrams under {root_rel} (baseline + scenarios)")
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
