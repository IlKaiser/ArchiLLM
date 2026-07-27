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
from src.plantuml_render import plantuml_image_url

REPORT_RELATIVE_PATH = "modifiability/report.json"
SCENARIOS_RELATIVE_PATH = "modifiability/scenarios.json"
ORIGINAL_DIAGRAM_RELATIVE_PATH = "component_diagram.puml"

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


def _scenarios_cached(project_name: str, run_dir: str = "run") -> bool:
    """Whether this project already has a saved scenarios.json — used only
    to pick an accurate spinner label (generating vs. loading) before a run,
    not to control run_modifiability's own caching behavior.
    """
    return (Path(run_dir) / project_name / SCENARIOS_RELATIVE_PATH).exists()


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


def _visualizable_scenarios(scenarios: list[dict]) -> list[dict]:
    """Scenarios with a real, on-disk rendered diagram to compare against the
    original — only "exact" (successfully-scored) scenarios qualify, since a
    failed/inconclusive one may have no diagram or a garbage one. Sorted by
    weighted_ged descending so the most illustrative example (the biggest
    change) is offered first.
    """
    return sorted(
        (s for s in scenarios if s.get("exact") and s.get("artifacts_dir")),
        key=lambda s: s["weighted_ged"],
        reverse=True,
    )


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


def _render_report(report: dict, project_name: str, key_suffix: str) -> None:
    """Render one modifiability report — shared by the preload-on-load path
    and the just-finished-a-run path, so both look identical.

    key_suffix: both call sites can execute in the SAME Streamlit script run
        (preload shows the existing report, then a button click renders a
        freshly-computed one further down) — every widget with an explicit
        key must stay unique across that pair of calls, or Streamlit raises
        a duplicate-key error.
    """
    n_nodes = report.get("original_node_count")
    n_edges = report.get("original_edge_count")
    if n_nodes is not None:
        st.caption(
            f"📐 Base graph (`{project_name}`'s current diagram): "
            f"**{n_nodes}** component(s), **{n_edges}** dependency edge(s)."
        )
    exec_time = report.get("execution_time_seconds")
    total_cost = report.get("total_cost_usd")
    if exec_time is not None:
        st.caption(f"⏱️ Took **{exec_time:.1f}s** · 💰 ~**${total_cost:.4f}**")

    st.metric(
        "Modifiability Score (lower = more flexible)",
        report["modifiability_score"],
        help=(
            "Average of each scenario's Weighted GED (Weight × Graph Edit "
            "Distance). A lower score means fewer/cheaper changes were "
            "needed, on average, to accommodate the generated future "
            "scenarios."
        ),
    )

    with st.expander("ℹ️ How to read this"):
        st.markdown(
            "- **Weight** (1-5): the LLM's estimate of how important or "
            "likely this future scenario is.\n"
            "- **Magnitude** (small / medium / large): the LLM's own "
            "estimate of how big a change the scenario would require — "
            "shown so you can sanity-check that bigger scenarios really "
            "do produce bigger distances.\n"
            "- **GED**: the real graph edit distance (via networkx) "
            "between the original component diagram and the one edited "
            "for this scenario — the minimum number of node/edge "
            "insertions, deletions, or substitutions needed.\n"
            "- **Weighted GED**: Weight × GED. The Modifiability Score above "
            "is the average of these across all successfully-scored "
            "scenarios.\n"
            "- **Exact**: whether the GED computation finished within "
            "its time budget. A scenario showing GED = “—” either failed "
            "(its LLM call errored, or it produced an unparseable "
            "diagram) or timed out — either way it's excluded from the "
            "Modifiability Score, not counted as zero or as a large "
            "distance."
        )

    chart = _scenario_chart(report["scenarios"])
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)
        st.caption("Bars are colored by magnitude — darker means a bigger expected change.")

    with st.expander("📋 Scenario table", expanded=chart is None):
        st.dataframe(_scenario_table_rows(report["scenarios"]), use_container_width=True)

    if report.get("by_magnitude"):
        st.markdown("#### Total Weighted GED by Magnitude")
        st.caption(
            "Sanity check: larger-magnitude scenarios should generally "
            "sum to a bigger total than smaller ones."
        )
        st.bar_chart(report["by_magnitude"])

    visualizable = _visualizable_scenarios(report["scenarios"])
    original_puml_path = Path("run") / project_name / ORIGINAL_DIAGRAM_RELATIVE_PATH
    if visualizable and original_puml_path.exists():
        st.markdown("#### 🔍 Visualize an Edit Distance Example")
        st.caption(
            "See what actually changed for one scenario — the original "
            "diagram side by side with the minimally-edited one. Sorted "
            "by biggest change first."
        )
        options = {
            f"{(s.get('description') or '')[:70]} (GED={s['ged']})": s
            for s in visualizable
        }
        choice = st.selectbox(
            "Choose a scenario to visualize",
            list(options.keys()),
            key=f"modifiability_visualize_select_{key_suffix}",
        )
        selected = options[choice]
        modified_puml_path = Path(selected["artifacts_dir"]) / "component_diagram.puml"

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Original**")
            st.image(
                plantuml_image_url(original_puml_path.read_text(encoding="utf-8")),
                use_container_width=True,
            )
        with col2:
            st.markdown(f"**Modified** (GED = {selected['ged']})")
            if modified_puml_path.exists():
                st.image(
                    plantuml_image_url(modified_puml_path.read_text(encoding="utf-8")),
                    use_container_width=True,
                )
            else:
                st.warning("Modified diagram artifact not found on disk.")


def render(project_name: str) -> None:
    st.markdown("---")
    st.subheader("🔀 Modifiability Analysis")
    st.caption(
        "Measures how much this architecture would need to change to support "
        "plausible future requirements. An LLM proposes new scenarios from the "
        "project's user stories, minimally edits the architecture for each one, "
        "and the real graph edit distance (via networkx) between the original "
        "and edited component diagrams is computed and weighted by how "
        "important each scenario is. **Lower total = more flexible.**"
    )

    if not project_name:
        st.info("Select a project above to run modifiability analysis.")
        return

    existing = _load_existing_report(project_name)
    if existing:
        st.caption(f"📁 Showing existing analysis for `{project_name}` from disk.")
        _render_report(existing, project_name, key_suffix="preload")

    regenerate = st.checkbox("🔄 Regenerate Analysis", value=False, key="chk_modifiability_regenerate")
    regenerate_scenarios = False
    if regenerate:
        regenerate_scenarios = st.checkbox(
            "🎲 Also generate new scenarios (instead of reusing the saved ones)",
            value=False,
            key="chk_modifiability_regenerate_scenarios",
            help=(
                "Once scenarios are generated for a project, they're saved and "
                "reused by default so re-scoring stays comparable across runs. "
                "Check this to roll a brand-new set instead."
            ),
        )

    if st.button("🔀 Run Modifiability Analysis", key="btn_run_modifiability"):
        if existing and not regenerate:
            st.info("Already showing the existing analysis above. Check 'Regenerate Analysis' to force a fresh run.")
        else:
            # Scenario generation is a single LLM call with no sub-steps to
            # report incrementally, so it gets an animated spinner (genuine
            # motion for an indeterminate wait) rather than sitting on a
            # progress bar frozen at 0% — the bar only becomes meaningful
            # once per-scenario scoring starts and on_progress fires.
            will_generate_fresh = regenerate_scenarios or not _scenarios_cached(project_name)
            spinner_label = (
                "Generating new scenarios…" if will_generate_fresh else "Loading saved scenarios…"
            )
            progress_bar = st.progress(0.0, text=spinner_label)

            def _on_progress(completed: int, total: int, result: dict) -> None:
                label = (result.get("description") or "")[:60]
                progress_bar.progress(completed / total, text=f"Scored {completed}/{total}: {label}")

            try:
                with st.spinner(spinner_label):
                    report = run_modifiability(
                        project_name, on_progress=_on_progress, regenerate_scenarios=regenerate_scenarios
                    )
                progress_bar.progress(1.0, text="Done.")
                st.success(
                    f"Analyzed {report['n_scenarios']} scenario(s) in "
                    f"{report.get('execution_time_seconds', 0):.1f}s "
                    f"(~${report.get('total_cost_usd', 0):.4f})."
                )
                _render_report(report, project_name, key_suffix="run")
            except FileNotFoundError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Modifiability analysis failed: {e}")
