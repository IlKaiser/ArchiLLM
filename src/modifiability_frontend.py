"""
modifiability_frontend.py — Streamlit section for running modifiability
analysis on the currently-selected project. Appended to app.py without
modifying its existing logic.
"""
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from Evaluation.modifiability import run as run_modifiability

REPORT_RELATIVE_PATH = "modifiability/report.json"

# Magnitude is ordinal (small < medium < large), not an arbitrary category, so
# it gets a fixed-order sequential color scale (one hue, light -> dark) rather
# than a free-cycled categorical palette — see the dataviz skill's color
# formula: "Sequential = one hue, light->dark."
MAGNITUDE_ORDER = ["small", "medium", "large"]


def _load_existing_report(project_name: str, run_dir: str = "run") -> dict | None:
    report_path = Path(run_dir) / project_name / REPORT_RELATIVE_PATH
    if not report_path.exists():
        return None
    return json.loads(report_path.read_text(encoding="utf-8"))


def _scenario_table_rows(scenarios: list[dict]) -> list[dict]:
    """Convert scenario dicts into row dicts suitable for st.dataframe."""
    rows = []
    for s in scenarios:
        rows.append({
            "Description": s.get("description", ""),
            "Weight": s.get("weight"),
            "Magnitude": s.get("magnitude"),
            "GED": s.get("ged") if s.get("ged") is not None else "—",
            "Weighted GED": s.get("weighted_ged") if s.get("weighted_ged") is not None else "—",
            "Exact": s.get("exact", False),
        })
    return rows


def _scenario_chart(scenarios: list[dict]) -> alt.Chart | None:
    """Horizontal bar chart of weighted GED per scenario, sorted descending,
    colored by magnitude on a fixed small->medium->large sequential scale
    (one hue, light->dark — magnitude is an ordinal size, not a free
    category), with a tooltip on every bar. Returns None if there are no
    scenarios with a computed weighted_ged to plot (e.g. every scenario
    errored or timed out).
    """
    rows = [
        {
            "Description": (s.get("description") or "")[:60],
            "Magnitude": s.get("magnitude", "unknown"),
            "Weighted GED": s.get("weighted_ged"),
            "GED": s.get("ged"),
            "Weight": s.get("weight"),
        }
        for s in scenarios
        if s.get("weighted_ged") is not None
    ]
    if not rows:
        return None

    df = pd.DataFrame(rows)
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Weighted GED:Q", title="Weighted Graph Edit Distance"),
            y=alt.Y("Description:N", sort="-x", title=None),
            color=alt.Color(
                "Magnitude:N",
                sort=MAGNITUDE_ORDER,
                scale=alt.Scale(domain=MAGNITUDE_ORDER, scheme="blues"),
                legend=alt.Legend(title="Magnitude"),
            ),
            tooltip=["Description", "Magnitude", "Weight", "GED", "Weighted GED"],
        )
        .properties(height=alt.Step(28))
    )


def render(project_name: str) -> None:
    st.markdown("---")
    st.subheader("🔀 Modifiability Analysis")

    if not project_name:
        st.info("Select a project above to run modifiability analysis.")
        return

    regenerate = st.checkbox("🔄 Regenerate Analysis", value=False, key="chk_modifiability_regenerate")

    if st.button("🔀 Run Modifiability Analysis", key="btn_run_modifiability"):
        existing = _load_existing_report(project_name)
        report = None
        if existing and not regenerate:
            st.info("Using existing analysis. Check 'Regenerate Analysis' to force a fresh run.")
            report = existing
        else:
            try:
                with st.spinner(f"Analyzing modifiability for {project_name}…"):
                    report = run_modifiability(project_name)
                st.success(f"Analyzed {report['n_scenarios']} scenario(s).")
            except FileNotFoundError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Modifiability analysis failed: {e}")

        if report is not None:
            st.metric("Modifiability Score (lower = more flexible)", report["modifiability_score"])

            chart = _scenario_chart(report["scenarios"])
            if chart is not None:
                st.altair_chart(chart, use_container_width=True)

            with st.expander("📋 Scenario table", expanded=chart is None):
                st.dataframe(_scenario_table_rows(report["scenarios"]), use_container_width=True)

            if report.get("by_magnitude"):
                st.markdown("#### Total Weighted GED by Magnitude")
                st.bar_chart(report["by_magnitude"])
