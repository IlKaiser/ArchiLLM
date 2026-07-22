"""
adr_frontend.py — Streamlit section for generating ADRs from the pattern
catalogue and scoring them with the DeepSeek judge. Appended to app.py
without modifying its existing diagram-pipeline logic.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from Evaluation.adr_judge import run as score_adrs
from src.adr_agent import run as generate_adrs

ADR_OUTPUT_DIR = "docs/adr"


def _list_existing_adrs(output_dir: str = ADR_OUTPUT_DIR) -> list[dict]:
    """Read any already-generated ADR markdown files off disk, sorted by filename."""
    out_dir = Path(output_dir)
    if not out_dir.exists():
        return []
    return [
        {"path": str(path), "content": path.read_text(encoding="utf-8")}
        for path in sorted(out_dir.glob("*.md"))
    ]


def _load_existing_scores(output_dir: str = ADR_OUTPUT_DIR) -> dict:
    scores_path = Path(output_dir) / "scores.json"
    if not scores_path.exists():
        return {}
    return json.loads(scores_path.read_text(encoding="utf-8"))


def _score_table_rows(scores: dict) -> list[dict]:
    """Convert the scores dict into row dicts suitable for st.dataframe."""
    return [
        {"Pattern": slug, "Score": f"{data.get('score', '—')}/5"}
        for slug, data in sorted(scores.items())
    ]


def render(default_llm_model: str) -> None:
    st.markdown("---")
    st.subheader("📜 Architecture Decision Records")
    st.caption(f"ADR generation uses LLM_MODEL: {default_llm_model}")

    regenerate = st.checkbox("🔄 Regenerate ADRs", value=False, key="chk_adr_regenerate")

    if st.button("📜 Generate ADRs from Pattern Catalogue", key="btn_gen_adr"):
        existing = _list_existing_adrs()
        if existing and not regenerate:
            st.info("Using existing ADRs. Check 'Regenerate ADRs' to force a fresh run.")
            adrs = existing
        else:
            try:
                with st.spinner("Generating ADRs from the pattern catalogue…"):
                    adrs = generate_adrs()
                st.success(f"Generated {len(adrs)} ADR(s).")
            except Exception as e:
                st.error(f"ADR generation failed: {e}")
                adrs = []
        for adr in adrs:
            title = Path(adr["path"]).stem
            with st.expander(title):
                st.markdown(adr["content"])

    st.markdown("#### 🧑‍⚖️ DeepSeek Judge")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not deepseek_key:
        st.warning("Set DEEPSEEK_API_KEY in the sidebar to enable ADR scoring.")
    elif st.button("🧑‍⚖️ Score ADRs with DeepSeek", key="btn_score_adr"):
        existing_scores = _load_existing_scores()
        if existing_scores and not regenerate:
            st.info("Using existing scores. Check 'Regenerate ADRs' to force a fresh run.")
            scores = existing_scores
        else:
            try:
                with st.spinner("Scoring ADRs with DeepSeek…"):
                    scores = score_adrs()
                st.success(f"Scored {len(scores)} ADR(s).")
            except Exception as e:
                st.error(f"ADR scoring failed: {e}")
                scores = {}
        st.dataframe(_score_table_rows(scores), use_container_width=True)
        for slug, data in sorted(scores.items()):
            with st.expander(f"{slug} — reasoning"):
                st.write(data.get("reasoning", ""))
                missing = data.get("missing_elements", [])
                if missing:
                    st.write("Missing elements:")
                    for item in missing:
                        st.write(f"- {item}")
