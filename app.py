import streamlit as st
import os
import sys
import queue
import threading
import contextlib
import zipfile
from io import BytesIO
from dotenv import load_dotenv

import zlib

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_EVAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Evaluation")
if _EVAL_DIR not in sys.path:
    sys.path.insert(0, _EVAL_DIR)

st.set_page_config(page_title="ARCHIv2 — Diagram Generator", layout="wide")


# ── PlantUML encoding helpers (deflate + base64 variant) ──────────────────
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


def zip_directory(folder_path):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    return zip_buffer.getvalue()


def run_diagram_agent_thread(diagram_prompt_obj, use_multi_agent, use_validator, q, local_llm_config=None):
    class QueueOut:
        def __init__(self, q, original):
            self.q = q
            self.original = original
        def write(self, text):
            self.q.put(text)
        def flush(self): pass
        def __getattr__(self, name):
            return getattr(self.original, name)

    with contextlib.redirect_stdout(QueueOut(q, sys.stdout)), \
         contextlib.redirect_stderr(QueueOut(q, sys.stderr)):
        try:
            from src.diagram_agent import run as run_diagram
            run_diagram(prompt=diagram_prompt_obj, use_multi_agent=use_multi_agent, use_validator=use_validator, local_llm_config=local_llm_config)
        except Exception as e:
            import traceback
            q.put(f"ERROR_FLAG:{str(e)}\n\n{traceback.format_exc()}")
        finally:
            q.put("DONE_FLAG")


# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Options")
use_multi_agent = st.sidebar.checkbox("Use Multi-Agent (EffortRouter)", value=False, key="chk_multi_agent")
use_validator = st.sidebar.checkbox("Enable Validation Agent (Agent 3)", value=False, key="chk_validator")
override = st.sidebar.checkbox("Override existing outputs", value=False, key="chk_override",
    help="If unchecked, skips diagram generation when outputs already exist and skips LLM eval when cache is present")

st.sidebar.markdown("---")
st.sidebar.title("🔑 LLM Configuration")

if st.sidebar.button("🔄 Reload Keys from .env"):
    load_dotenv(override=True)
    st.sidebar.success("Loaded from .env!")
    st.rerun()

# ── Local inference toggle
use_local_llm = st.sidebar.checkbox("⚡ Use Local Model (Ollama / HuggingFace)", value=False, key="chk_local_llm")
local_llm_config = None
if use_local_llm:
    st.sidebar.subheader("Local Inference")
    local_backend = st.sidebar.selectbox("Backend", ["ollama", "huggingface"], key="local_backend")
    local_model = st.sidebar.text_input(
        "Model name",
        value="qwen2.5-coder:32b" if local_backend == "ollama" else "mistralai/Mistral-7B-Instruct-v0.3",
        key="local_model",
    )
    _default_url = "http://localhost:11434" if local_backend == "ollama" else "http://localhost:8080"
    local_url = st.sidebar.text_input("Server URL", value=_default_url, key="local_url")
    try:
        from src.local_llm import get_local_llm_config
        local_llm_config = get_local_llm_config(backend=local_backend, model=local_model, base_url=local_url or None)
        st.sidebar.success(f"Local: {local_llm_config['model']}")
    except Exception as _e:
        st.sidebar.error(str(_e))

st.sidebar.subheader("Primary LLM (Cloud)")
llm_model = st.sidebar.text_input("LLM_MODEL", value=os.environ.get("LLM_MODEL", "moonshot/kimi-k2.6"), disabled=use_local_llm)
llm_api_key = st.sidebar.text_input("LLM_API_KEY", type="password", value=os.environ.get("LLM_API_KEY", ""), disabled=use_local_llm)
llm_base_url = st.sidebar.text_input("LLM_JUDGE_URL", value=os.environ.get("LLM_JUDGE_URL", "https://api.openai.com/v1"), help="OpenAI-compatible base URL for the judge LLM")
llm_judge_key = st.sidebar.text_input("LLM_JUDGE_KEY", type="password", value=os.environ.get("LLM_JUDGE_KEY", ""), help="API key for the judge LLM (falls back to LLM_API_KEY if blank)")
llm_judge_model = st.sidebar.text_input("JUDGE_MODEL", value=os.environ.get("JUDGE_MODEL", "gpt-5.5"), help="Model used for LLM-as-a-judge evaluation")

secondary_llm_model = os.environ.get("SECONDARY_LLM_MODEL", "openhands/devstral-medium-2507")
secondary_llm_api_key = os.environ.get("SECONDARY_LLM_API_KEY", "")

if use_multi_agent:
    st.sidebar.subheader("Secondary LLM")
    secondary_llm_model = st.sidebar.text_input("SECONDARY_LLM_MODEL", value=secondary_llm_model)
    secondary_llm_api_key = st.sidebar.text_input("SECONDARY_LLM_API_KEY", type="password", value=secondary_llm_api_key)

if st.sidebar.button("💾 Save Keys to Environment"):
    os.environ["LLM_MODEL"] = llm_model
    os.environ["LLM_API_KEY"] = llm_api_key
    os.environ["LLM_JUDGE_URL"] = llm_base_url
    os.environ["LLM_JUDGE_KEY"] = llm_judge_key
    os.environ["JUDGE_MODEL"] = llm_judge_model
    os.environ["SECONDARY_LLM_MODEL"] = secondary_llm_model
    os.environ["SECONDARY_LLM_API_KEY"] = secondary_llm_api_key
    st.sidebar.success("Saved dynamically to process environment!")

# ── Main ───────────────────────────────────────────────────────────────────
st.title("🏄🏼‍♀️ ARCHIv2 — UML Component Diagram Generator")

dataset_base = os.path.join(os.getcwd(), "dataset", "student_projects")
available_projects = sorted(
    p for p in os.listdir(dataset_base)
    if os.path.isdir(os.path.join(dataset_base, p))
) if os.path.exists(dataset_base) else []

proj_name = st.selectbox(
    "Select Dataset Project",
    options=[""] + available_projects,
    index=0,
    key="proj_select",
)

if proj_name:
    input_path = os.path.join(dataset_base, proj_name, "input.txt")
    if os.path.exists(input_path):
        with open(input_path, "r", encoding="utf-8") as f:
            st.text_area("Project Input Preview", value=f.read(), height=150, disabled=True)
    st.info(
        f"📐 Input read from `dataset/student_projects/{proj_name}/`. "
        f"Outputs saved to `run/{proj_name}/`."
    )

st.markdown("---")

execute_trigger = st.button("📐 Run Diagram Pipeline", type="primary")

if execute_trigger:
    if not proj_name:
        st.error("Please select a project.")
    elif not llm_api_key:
        st.error("LLM_API_KEY is required in the sidebar.")
    elif not st.session_state.get("is_running", False):
        _existing_puml = os.path.join(os.getcwd(), "run", proj_name, "component_diagram.puml")
        if not override and os.path.exists(_existing_puml):
            st.session_state.show_results = True
            st.session_state.setdefault("is_running", False)
            st.session_state.setdefault("has_error", False)
            st.session_state.setdefault("error_message", "")
            st.session_state.setdefault("full_logs", "")
            st.session_state.setdefault("zip_bytes", None)
            st.session_state.setdefault("completed_steps", {"extract": True, "render": True, "validate": False})
            st.rerun()
        from src.prompt import DiagramPrompt
        diagram_prompt_obj = DiagramPrompt(title=proj_name)
        st.session_state.is_running = True
        st.session_state.show_results = False
        st.session_state.q = queue.Queue()
        st.session_state.full_logs = ""
        st.session_state.has_error = False
        st.session_state.error_message = ""
        st.session_state.zip_bytes = None
        st.session_state.completed_steps = {"extract": False, "render": False, "validate": False}
        st.session_state.thread = threading.Thread(
            target=run_diagram_agent_thread,
            args=(diagram_prompt_obj, use_multi_agent, use_validator, st.session_state.q),
            kwargs={"local_llm_config": local_llm_config},
            daemon=True,
        )
        st.session_state.thread.start()

if st.session_state.get("is_running", False) or st.session_state.get("show_results", False):
    st.markdown("---")
    st.warning("⚠️ Diagram generation can take several minutes. Do not refresh the page.")
    metrics_container = st.container()

    with st.status(
        "Pipeline running…" if st.session_state.get("is_running") else "Pipeline complete",
        expanded=True,
    ) as status:
        log_area = st.empty()
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        if st.session_state.get("is_running"):
            while True:
                try:
                    raw_text = st.session_state.q.get(timeout=1.0)
                    if raw_text == "DONE_FLAG":
                        st.session_state.is_running = False
                        st.session_state.show_results = True
                        break

                    text = ansi_escape.sub('', raw_text)
                    if text.startswith("ERROR_FLAG:"):
                        st.session_state.has_error = True
                        st.session_state.error_message = text.replace("ERROR_FLAG:", "")
                        continue

                    if "--- STEP_METRICS:" in text:
                        m_info = text.split("--- STEP_METRICS:")[-1].split("---")[0].strip()
                        metrics_container.info(f"⏱️ Step completed: **{m_info}**")
                        if "Architecture Extraction" in m_info:
                            st.session_state.completed_steps["extract"] = True
                        elif "Diagram Rendering" in m_info:
                            st.session_state.completed_steps["render"] = True
                        elif "Validation" in m_info:
                            st.session_state.completed_steps["validate"] = True
                    if "--- FINAL_METRICS:" in text:
                        m_info = text.split("--- FINAL_METRICS:")[-1].split("---")[0].strip()
                        metrics_container.success(f"🏆 Total: **{m_info}**")

                    st.session_state.full_logs += text
                    log_area.code(st.session_state.full_logs[-3000:], language="bash")
                except queue.Empty:
                    pass
        else:
            log_area.code(st.session_state.full_logs[-3000:], language="bash")

        if st.session_state.get("has_error", False):
            status.update(label="Pipeline failed!", state="error", expanded=True)
        else:
            status.update(label="Pipeline complete!", state="complete", expanded=False)

    if st.session_state.get("has_error", False):
        st.error("🚨 Pipeline failed!")
        st.code(st.session_state.get("error_message", ""), language="text")
    else:
        _was_skipped = not st.session_state.get("is_running", False) and st.session_state.get("completed_steps", {}).get("extract") is True and not st.session_state.get("full_logs", "")
        if _was_skipped:
            st.info("⚡ Existing outputs loaded — pipeline skipped. Check **Override existing outputs** to regenerate.")
        else:
            st.success("Pipeline finished successfully!")
        run_folder = os.path.join(os.getcwd(), "run", proj_name)
        if os.path.exists(run_folder):
            # ── PlantUML visualizer ────────────────────────────────────────
            puml_path = os.path.join(run_folder, "component_diagram.puml")
            if os.path.exists(puml_path):
                with open(puml_path, "r", encoding="utf-8") as f:
                    puml_text = f.read()

                st.subheader("📊 Component Diagram")
                encoded = plantuml_encode(puml_text)
                server_url = f"https://www.plantuml.com/plantuml/png/{encoded}"
                st.image(server_url, use_container_width=True)

                with st.expander("View PlantUML source"):
                    st.code(puml_text, language="text")
            else:
                st.warning("component_diagram.puml not found in output folder.")

            # ── Architecture summary ───────────────────────────────────────
            summary_path = os.path.join(run_folder, "architecture_summary.md")
            if os.path.exists(summary_path):
                with open(summary_path, "r", encoding="utf-8") as f:
                    summary_text = f.read()
                with st.expander("📄 Architecture Summary", expanded=False):
                    st.markdown(summary_text)

            # ── Structural evaluation ────────────────────────────────────
            ref_path = os.path.join(dataset_base, proj_name, "ref.wsd")
            if os.path.exists(ref_path) and os.path.exists(puml_path):
                st.subheader("📏 Diagram Evaluation")
                try:
                    from uml_parser import UMLParser as _UMLParser
                    from metrics_calculator import MetricsCalculator as _MetricsCalculator
                    from llm_judge import LLMJudge as _LLMJudge
                    from arch_scorer import ArchScorer as _ArchScorer

                    _parser = _UMLParser()
                    _gt = _parser.parse(open(ref_path, encoding="utf-8").read())
                    _pred_eval = _parser.parse(puml_text)

                    _no_llm_align = {
                        "matched_pairs": [],
                        "unmatched_gt_nodes": _gt["leafnodes"],
                        "unmatched_predicted_nodes": _pred_eval["leafnodes"],
                    }
                    _calc = _MetricsCalculator()
                    import io as _io, contextlib as _cl
                    with _cl.redirect_stdout(_io.StringIO()):
                        _calc.evaluate_project(
                            project_name=proj_name,
                            gt_parsed=_gt,
                            pred_parsed=_pred_eval,
                            alignment_data=_no_llm_align,
                        )
                    _res = _calc.results[0]

                    st.markdown("---")

                    # ─ LLM evaluation ─────────────────────────────────────
                    _eval_out = os.path.join(_EVAL_DIR, "outputs", proj_name)
                    _j_cache  = os.path.join(_eval_out, "judge_alignment.json")
                    _s_cache  = os.path.join(_eval_out, "arch_score.json")
                    _prd_text = open(os.path.join(dataset_base, proj_name, "input.txt"), encoding="utf-8").read() \
                        if os.path.exists(os.path.join(dataset_base, proj_name, "input.txt")) else ""
                    _has_cache = os.path.exists(_j_cache) and os.path.exists(_s_cache)

                    if _has_cache:
                        _align     = __import__("json").loads(open(_j_cache, encoding="utf-8").read())
                        _score_res = __import__("json").loads(open(_s_cache, encoding="utf-8").read())

                        if not _score_res:
                            st.error("🚨 Scoring cache is empty — the previous run failed silently. Clear cache and re-run.")
                            if st.button("🗑️ Clear Bad Cache", key="btn_clear_bad"):
                                for _f in [_j_cache, _s_cache]:
                                    if os.path.exists(_f): os.remove(_f)
                                st.rerun()
                            _has_cache = False

                    if _has_cache:
                        _calc2 = _MetricsCalculator()
                        with _cl.redirect_stdout(_io.StringIO()):
                            _calc2.evaluate_project(
                                project_name=proj_name,
                                gt_parsed=_gt, pred_parsed=_pred_eval,
                                alignment_data=_align,
                            )
                        _r2 = _calc2.results[0]
                        _dim = _ArchScorer.extract_scores(_score_res)

                        _sv = 1 if len(_pred_eval["nodes"]) > 0 and len(_pred_eval["edges"]) > 0 else 0

                        def _fmt(v, decimals=3):
                            return f"{v:.{decimals}f}" if v is not None else "—"
                        def _fmti(v):
                            return str(int(v)) if v is not None else "—"

                        _html_table = f"""
<style>
.eval-tbl{{border-collapse:collapse;width:100%;font-size:13px;font-family:monospace}}
.eval-tbl th,.eval-tbl td{{border:1px solid #ddd;padding:5px 10px;text-align:center;white-space:nowrap}}
.eval-tbl .gh{{background:#dce3f5;font-weight:700;font-size:12px;letter-spacing:.5px}}
.eval-tbl th{{background:#f0f2f6;font-weight:600}}
.eval-tbl td{{background:#fafafa}}
</style>
<table class="eval-tbl">
  <tr>
    <th rowspan="2">Model</th>
    <th rowspan="2">Framework</th>
    <th colspan="5" class="gh">Layer 1: Structural Graph Metrics</th>
    <th colspan="4" class="gh">Layer 2: Judge Scores</th>
    <th colspan="2" class="gh">Layer 3: Anti-pattern</th>
  </tr>
  <tr>
    <th>SV</th><th>Node F1</th><th>Edge F1</th><th>GED</th><th>Layer</th>
    <th>Comp.</th><th>Acc.</th><th>Rat.</th><th>Read.</th>
    <th>R<sub>orphan</sub></th><th>R<sub>god</sub></th>
  </tr>
  <tr>
    <td>{llm_model}</td>
    <td>{proj_name}</td>
    <td>{_sv}</td>
    <td>{_fmt(_r2["Node_F1"])}</td>
    <td>{_fmt(_r2["Edge_F1"])}</td>
    <td>{_fmt(_r2["GED"] / 100)}</td>
    <td>{_fmt(_r2["Boundary_Accuracy"])}</td>
    <td>{_fmti(_dim["Score_Completeness"])}</td>
    <td>{_fmti(_dim["Score_Accuracy"])}</td>
    <td>{_fmti(_dim["Score_Rationality"])}</td>
    <td>{_fmti(_dim["Score_Readability"])}</td>
    <td>{_fmt(_res["Orphan_Ratio"])}</td>
    <td>{_fmt(_res["God_Ratio"])}</td>
  </tr>
</table>
"""
                        st.subheader("📊 Evaluation Results")
                        st.markdown(_html_table, unsafe_allow_html=True)

                        _cot = _score_res.get("chain_of_thought", "")
                        if _cot:
                            with st.expander("🧠 LLM Reasoning"):
                                st.write(_cot)
                        with st.expander("📋 Score Breakdown"):
                            for _dkey, _dlabel in [("completeness","Completeness"),("accuracy","Accuracy"),("rationality","Rationality"),("readability","Readability")]:
                                _d = _score_res.get("scores", {}).get(_dkey, {})
                                if _d:
                                    st.markdown(f"**{_dlabel} ({_d.get('score','?')}/5):** {_d.get('reasoning','')}")

                        _csv_path = os.path.join(_eval_out, "eval_results.csv")
                        if os.path.exists(_csv_path):
                            import pandas as _pd
                            with st.expander("📊 Full Metrics Table", expanded=False):
                                st.dataframe(_pd.read_csv(_csv_path), use_container_width=True)

                        st.caption(f"⚡ From cache: `{_eval_out}`")
                        if st.button("🗑️ Clear Cache & Re-run", key="btn_llm_clear"):
                            for _f in [_j_cache, _s_cache]:
                                if os.path.exists(_f): os.remove(_f)
                            st.rerun()

                    else:
                        _raw_model    = llm_judge_model
                        _eval_model   = _raw_model.split("/", 1)[1] if "/" in _raw_model else _raw_model
                        _eval_base    = llm_base_url or "https://api.openai.com/v1"
                        _judge_api_key = llm_judge_key or llm_api_key

                        if not _judge_api_key:
                            st.warning("⚠️ Set LLM_JUDGE_KEY (or LLM_API_KEY) in the sidebar to enable LLM evaluation.")
                        else:
                            os.makedirs(_eval_out, exist_ok=True)
                            with st.spinner("🧠 Running semantic alignment…"):
                                _judge = _LLMJudge(api_key=_judge_api_key, base_url=_eval_base, model_name=_eval_model)
                                _align = _judge.evaluate_alignment(
                                    prd_summary=_prd_text[:3000],
                                    gt_nodes=_gt["leafnodes"],
                                    predicted_nodes=_pred_eval["leafnodes"],
                                )
                                open(_j_cache, "w", encoding="utf-8").write(
                                    __import__("json").dumps(_align, indent=2, ensure_ascii=False))
                            _orig = os.getcwd()
                            os.chdir(_EVAL_DIR)
                            try:
                                with st.spinner("📝 Running rubric scoring…"):
                                    _scorer = _ArchScorer(api_key=_judge_api_key, base_url=_eval_base, model_name=_eval_model)
                                    _score_res = _scorer.score(prd_text=_prd_text, predicted_puml=puml_text)
                                    if not _score_res:
                                        raise ValueError("ArchScorer returned an empty result — check model name, API key, and base URL.")
                                    open(_s_cache, "w", encoding="utf-8").write(
                                        __import__("json").dumps(_score_res, indent=2, ensure_ascii=False))
                            finally:
                                os.chdir(_orig)
                            st.rerun()

                except Exception as _e:
                    import traceback as _tb
                    st.warning(f"Evaluation error: {_e}")
                    with st.expander("Traceback"):
                        st.code(_tb.format_exc())

            # ── Download ───────────────────────────────────────────────────
            if not st.session_state.get("zip_bytes"):
                with st.spinner("Packaging outputs…"):
                    st.session_state.zip_bytes = zip_directory(run_folder)
            st.download_button(
                label=f"📦 Download {proj_name} Diagram Outputs (.zip)",
                data=st.session_state.zip_bytes,
                file_name=f"{proj_name}_diagram.zip",
                mime="application/zip",
            )
        else:
            st.error("Output folder not found — the pipeline may have failed silently.")
