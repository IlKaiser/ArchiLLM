import streamlit as st
import os
import sys
import shutil
import queue
import threading
import contextlib
import zipfile
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# Make sure src is in pythonpath
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="ARTHUR Orchestrator", layout="wide")

# Default values for preloaded case
PRELOAD_TITLE = "easybank"
PRELOAD_DESC = """A bank offers various types of accounts to its customers. The customer can open an account, deposit money, withdraw money, and close the account. An account can have multiple owners. An owner can own multiple accounts. An owner is identified by a unique ID, a name, and an address. An account is identified by a unique account number and has a balance. The balance is updated upon deposit and withdrawal. A withdrawal is only allowed if the balance is sufficient. When the account is closed, the balance must be zero."""

def zip_directory(folder_path):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    return zip_buffer.getvalue()

def run_agent_thread(prompt_obj, kwargs, q):
    import sys
    class QueueOut:
        def __init__(self, q, original):
            self.q = q
            self.original = original
        def write(self, text):
            self.q.put(text)
        def flush(self): pass
        def __getattr__(self, name):
            return getattr(self.original, name)

    with contextlib.redirect_stdout(QueueOut(q, sys.stdout)), contextlib.redirect_stderr(QueueOut(q, sys.stderr)):
        try:
            from src.agent import run
            run(prompt=prompt_obj, **kwargs)
        except Exception as e:
            import traceback
            q.put(f"ERROR_FLAG:{str(e)}\n\n{traceback.format_exc()}")
        finally:
            q.put("DONE_FLAG")

# Sidebar Configuration
st.sidebar.title("⚙️ Generation Modes")
create_backend = st.sidebar.checkbox("Create Backend", value=True)
create_frontend = st.sidebar.checkbox("Create Frontend", value=True)
create_test = st.sidebar.checkbox("Create Test Suite", value=True)
use_spring_boot = st.sidebar.checkbox("Use Spring Boot (Java)", value=True)
use_multi_agent = st.sidebar.checkbox("Use Multi-Agent (Delegation)", value=False)
st.sidebar.markdown("*(Note: For Python backends, uncheck 'Use Spring Boot')*")

st.sidebar.markdown("---")
st.sidebar.title("🔑 LLM Configuration")

if st.sidebar.button("🔄 Reload Keys from .env"):
    load_dotenv(override=True)
    st.sidebar.success("Loaded from .env!")
    st.rerun()

st.sidebar.subheader("Primary LLM")
llm_model = st.sidebar.text_input("LLM_MODEL", value=os.environ.get("LLM_MODEL", "moonshot/kimi-k2.5"))
llm_api_key = st.sidebar.text_input("LLM_API_KEY", type="password", value=os.environ.get("LLM_API_KEY", ""))

secondary_llm_model = os.environ.get("SECONDARY_LLM_MODEL", "openhands/devstral-medium-2507")
secondary_llm_api_key = os.environ.get("SECONDARY_LLM_API_KEY", "")

if use_multi_agent:
    st.sidebar.subheader("Secondary LLM")
    secondary_llm_model = st.sidebar.text_input("SECONDARY_LLM_MODEL", value=secondary_llm_model)
    secondary_llm_api_key = st.sidebar.text_input("SECONDARY_LLM_API_KEY", type="password", value=secondary_llm_api_key)

st.sidebar.subheader("Test LLM")
test_llm_model = st.sidebar.text_input("TEST_LLM_MODEL", value=os.environ.get("TEST_LLM_MODEL", "moonshot/kimi-k2.5"))
test_llm_api_key = st.sidebar.text_input("TEST_LLM_API_KEY", type="password", value=os.environ.get("TEST_LLM_API_KEY", ""))

if st.sidebar.button("💾 Save Keys to Environment"):
    os.environ["LLM_MODEL"] = llm_model
    os.environ["LLM_API_KEY"] = llm_api_key
    os.environ["SECONDARY_LLM_MODEL"] = secondary_llm_model
    os.environ["SECONDARY_LLM_API_KEY"] = secondary_llm_api_key
    os.environ["TEST_LLM_MODEL"] = test_llm_model
    os.environ["TEST_LLM_API_KEY"] = test_llm_api_key
    st.sidebar.success("Saved dynamically to process environment!")

# Main Content
st.title("🤖 MultiMultiAgent-ArchiLLM Console")

if st.button("🚀 Preload 'EasyBank' specific case (Default)"):
    st.session_state["proj_name"] = PRELOAD_TITLE
    st.session_state["proj_desc"] = PRELOAD_DESC
    st.rerun()

proj_name = st.text_input("Project Name (Title)", value=st.session_state.get("proj_name", ""))
proj_desc = st.text_area("Textual Description", value=st.session_state.get("proj_desc", ""), height=150)

merode_path = os.path.join(os.getcwd(), "projects", proj_name, "merode_application") if proj_name else ""

if merode_path:
    xmp_file_path = os.path.join(merode_path, "model.xmp")
    if os.path.exists(xmp_file_path):
        st.info("📌 `model.xmp` successfully detected in the existing project folder.")

st.subheader("📁 Project Data Input Mode")
input_mode = st.radio("Choose Backend Generation Input Strategy:", [
    "From Natural Language Description Only (No Files Needed)",
    "From MERODE Conceptual Model (model.mxp)",
    "From Java DAO Files (.java)"
], index=1)

use_backend_from_description = False
create_backend_only_uml = False

if input_mode == "From Natural Language Description Only (No Files Needed)":
    use_backend_from_description = True
    st.info("The backend agent will derive everything from the textual description.")
    
elif input_mode == "From MERODE Conceptual Model (model.mxp)":
    create_backend_only_uml = True
    xmp_file_path = os.path.join(merode_path, "model.mxp") if merode_path else ""
    if xmp_file_path and os.path.exists(xmp_file_path):
        st.success("✅ Ready to use preloaded `model.mxp`.")
    uploaded_xmp = st.file_uploader("Upload model.mxp (optional if preloaded)", type=["mxp"])
    if uploaded_xmp and proj_name:
        os.makedirs(merode_path, exist_ok=True)
        with open(os.path.join(merode_path, "model.mxp"), "wb") as f:
            f.write(uploaded_xmp.getbuffer())
        st.success("Saved model.mxp to project folder.")
        
elif input_mode == "From Java DAO Files (.java)":
    uploaded_daos = st.file_uploader("Upload Java DAO files or a .zip file", type=["java", "zip"], accept_multiple_files=True)
    if uploaded_daos and proj_name:
        project_root_path = os.path.join(os.getcwd(), "projects", proj_name)
        os.makedirs(project_root_path, exist_ok=True)
        for dao in uploaded_daos:
            if dao.name.endswith(".zip"):
                with zipfile.ZipFile(dao, "r") as zip_ref:
                    zip_ref.extractall(project_root_path)
            else:
                dao_path = os.path.join(merode_path, "src", "dao")
                os.makedirs(dao_path, exist_ok=True)
                with open(os.path.join(dao_path, dao.name), "wb") as f:
                    f.write(dao.getbuffer())
        st.success(f"Processed uploaded source code file(s).")

st.markdown("---")
# Common files (like Tests)
tc_path = os.path.join(merode_path, f"{proj_name}_testcases.html") if merode_path else ""
if tc_path and os.path.exists(tc_path):
    st.success(f"✅ Found existing `{proj_name}_testcases.html` preloaded.")
uploaded_testcase = st.file_uploader("Upload Testcases HTML (optional if preloaded)", type=["html"])
if uploaded_testcase and proj_name:
    os.makedirs(merode_path, exist_ok=True)
    with open(os.path.join(merode_path, f"{proj_name}_testcases.html"), "wb") as f:
        f.write(uploaded_testcase.getbuffer())
    st.success("Saved testcases HTML.")

st.markdown("---")

if st.button("🔨 Run AI Agent Generator", type="primary"):
    if not proj_name or not proj_desc:
        st.error("Project Name and Description are required.")
    elif not llm_api_key:
        st.error("LLM_API_KEY is required in the sidebar.")
    else:
        # Create Prompt 
        from src.prompt import Prompt
        prompt_obj = Prompt(title=proj_name, desc=proj_desc)
        
        # Prepare kwargs
        kwargs = {
            "create_backend": create_backend,
            "create_backend_only_uml": create_backend_only_uml,
            "create_frontend": create_frontend,
            "create_test": create_test,
            "use_spring_boot": use_spring_boot,
            "use_backend_from_description": use_backend_from_description,
            "use_multi_agent": use_multi_agent
        }

        # Setup streaming execution loop
        q = queue.Queue()
        thread = threading.Thread(target=run_agent_thread, args=(prompt_obj, kwargs, q), daemon=True)
        
        st.warning("⚠️ Generation can take several minutes to completely build and test. Please do not refresh the page.")
        
        metrics_container = st.container()
        
        with st.status("Agent Orchestrator Running...", expanded=True) as status:
            log_area = st.empty()
            full_logs = ""
            has_error = False
            error_message = ""
            
            thread.start()
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            
            while True:
                try:
                    raw_text = q.get(timeout=1.0)
                    if raw_text == "DONE_FLAG":
                        break
                    
                    # Strip ANSI terminal color codes for a clean UI
                    text = ansi_escape.sub('', raw_text)
                    
                    if text.startswith("ERROR_FLAG:"):
                        has_error = True
                        error_message = text.replace("ERROR_FLAG:", "")
                        continue
                        
                    if "--- STEP_METRICS:" in text:
                        m_info = text.split("--- STEP_METRICS:")[-1].split("---")[0].strip()
                        metrics_container.info(f"⏱️ Step Completed: **{m_info}**")
                        
                    if "--- FINAL_METRICS:" in text:
                        m_info = text.split("--- FINAL_METRICS:")[-1].split("---")[0].strip()
                        metrics_container.success(f"🏆 Execution Aggregates: **{m_info}**")
                        
                    full_logs += text
                    # We only display the last 3000 chars to avoid UI lag
                    display_text = full_logs[-3000:]
                    log_area.code(display_text, language="bash")
                except queue.Empty:
                    pass
            
            if has_error:
                status.update(label="Process failed!", state="error", expanded=True)
            else:
                status.update(label="Process complete!", state="complete", expanded=False)
            
        if has_error:
            st.error("🚨 Generation failed due to an error!")
            st.code(error_message, language="text")
        else:
            st.success("Agents have successfully finished processing!")
            
            # Provide Download Option
            run_folder = os.path.join(os.getcwd(), "run", proj_name)
            if os.path.exists(run_folder):
                with st.spinner("Wait, packaging the generated project into a zip file..."):
                    zip_bytes = zip_directory(run_folder)
                    
                st.download_button(
                    label=f"📦 Download {proj_name} Generated Files (.zip)",
                    data=zip_bytes,
                    file_name=f"{proj_name}_generated.zip",
                    mime="application/zip"
                )
            else:
                st.error("Run output folder not found. There might have been an execution error that was not caught.")
