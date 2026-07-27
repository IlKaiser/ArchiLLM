import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modifiability_frontend import _render_report

# "4-by-4" already has a real run/4-by-4/component_diagram.puml on disk, so
# the "Visualize an Edit Distance Example" selectbox (the widget that was
# hitting the duplicate-key error) actually renders for both calls below —
# simulating the preload-then-post-run sequence that happens in one script
# pass when render() shows an existing report and then a button click
# renders a freshly-computed one further down the page.
_FAKE_REPORT = {
    "modifiability_score": 5.0,
    "original_node_count": 3,
    "original_edge_count": 2,
    "execution_time_seconds": 1.0,
    "total_cost_usd": 0.01,
    "by_magnitude": {"small": 5.0},
    "scenarios": [
        {
            "description": "A scenario",
            "weight": 1,
            "magnitude": "small",
            "ged": 5.0,
            "exact": True,
            "weighted_ged": 5.0,
            "artifacts_dir": "run/4-by-4/modifiability/scenario_01",
        },
    ],
}

_render_report(_FAKE_REPORT, "4-by-4", key_suffix="preload")
_render_report(_FAKE_REPORT, "4-by-4", key_suffix="run")
