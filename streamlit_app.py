import streamlit as st
import subprocess
import sys
import time
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="The Digital Forge",
    page_icon="🛠️",
    layout="wide"
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    /* Customizing the header */
    .st-emotion-cache-18ni7ap {
        background-color: #f0f2f6;
    }
    /* Styling for the status boxes */
    .status-box {
        border: 1px solid #e0e0e0;
        border-left-width: 5px;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease-in-out;
    }
    .status-box-pending { border-left-color: #cccccc; }
    .status-box-working { border-left-color: #007bff; }
    .status-box-success { border-left-color: #28a745; }
    .status-box-warning { border-left-color: #ffc107; }
    .status-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper function for styled status updates ---
def styled_status(icon, text, status="pending"):
    return f"""
    <div class=\"status-box status-box-{status}\">\n        <div class=\"status-icon\">{icon}</div>\n        <div>{text}</div>\n    </div>
    """

# --- Initialize Session State ---
if 'pipeline_run_details' not in st.session_state:
    st.session_state.pipeline_run_details = {}

# --- App Header ---
st.title("🛠️ The Digital Forge")
st.caption("Your AI-Powered Software Development Crew")
st.write(
    "Welcome! Describe the code you need, and our AI crew will build and test it. "
    "For best results, please make your request as detailed as possible."
)
st.divider()

# --- Main Layout (Two Columns) ---
col1, col2 = st.columns([1, 1.2], gap="large")
with col1:
    st.subheader("1. Your Request")
    user_request = st.text_area(
        "**Describe the code you want the agents to write:**",
        height= 200, #259,
        placeholder="e.g., I need a Python function called `calculate_sum` in a file named `math_utils.py` that takes a list of numbers and returns their sum."
    )
    start_button = st.button("Start Forging", type="primary", use_container_width=True)
    stop_button = st.button("Stop Forging", type="secondary", use_container_width=True)

with col2:
    st.subheader("2. Pipeline Status")
    # Display elapsed time if available
    if 'start_time' in st.session_state:
        elapsed = time.time() - st.session_state.start_time
        st.markdown(f"**Elapsed Time:** {elapsed:.1f}s")
    status_area = st.container(height=400)

# --- Logic to handle stop button ---
if stop_button:
    st.session_state.pipeline_run_details = {}
    st.session_state.pop('start_time', None)
    st.rerun()

# --- Logic to handle button click and pipeline execution ---
if start_button:
    if not user_request.strip():
        st.warning("Please enter a request before starting the forge.")
    else:
        # Record start time
        st.session_state.start_time = time.time()
        st.session_state.pipeline_run_details = {
            "output": [],
            "status": "running",
            "return_code": None,
            "user_request": user_request
        }
        st.rerun()

# --- Main display logic based on session state ---
status = st.session_state.pipeline_run_details.get("status")

def render_status():
    with status_area:
        if status == "completed":
            for line in st.session_state.pipeline_run_details.get("output", []):
                cleaned = line.strip()
                if not cleaned:
                    continue
                if "DONE: Janus: Clarifying" in cleaned:
                    st.markdown(styled_status("✅", "Janus has clarified the requirements.", "success"), unsafe_allow_html=True)
                elif "DONE: Athena: Deconstructing" in cleaned:
                    st.markdown(styled_status("✅", "Athena has structured the development plan.", "success"), unsafe_allow_html=True)
                elif "DONE: Hephaestus: Writing" in cleaned:
                    st.markdown(styled_status("✅", "Hephaestus has finished the code.", "success"), unsafe_allow_html=True)
                elif "DONE: Argus: Creating" in cleaned:
                    st.markdown(styled_status("✅", "Argus confirmed all tests passed.", "success"), unsafe_allow_html=True)
                elif "DONE: Athena: Analyzing" in cleaned:
                    st.markdown(styled_status("✅", "Athena has created a bug report.", "success"), unsafe_allow_html=True)
                elif "START: Janus: Compiling" in cleaned:
                    st.markdown(styled_status("📄", "Janus is now building the final report...", "working"), unsafe_allow_html=True)
                elif "DONE: Janus: Compiling" in cleaned or "---FINAL_REPORT---" in cleaned:
                    st.markdown(styled_status("✅", "Janus has created the final report.", "success"), unsafe_allow_html=True)

if status in ("running", "completed"):
    render_status()

# --- Running logic ---
if status == "running":
    with status_area:
        placeholders = {}
        sprint_attempt = 1
        current_request = st.session_state.pipeline_run_details.get("user_request", "")
        try:
            process = subprocess.Popen(
                [sys.executable, "backend/main-deployment.py", current_request],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8'
            )
            for line in process.stdout:
                cleaned_line = line.strip()
                if not cleaned_line:
                    continue
                st.session_state.pipeline_run_details["output"].append(cleaned_line)
                if "START: Janus: Clarifying" in cleaned_line:
                    placeholders["janus_brief"] = st.empty()
                    placeholders["janus_brief"].markdown(styled_status("🤔", "Janus is understanding the request...", "working"), unsafe_allow_html=True)
                elif "DONE: Janus: Clarifying" in cleaned_line:
                    placeholders["janus_brief"].markdown(styled_status("✅", "Janus has clarified the requirements.", "success"), unsafe_allow_html=True)
                elif "START: Athena: Deconstructing" in cleaned_line:
                    placeholders["athena_plan"] = st.empty()
                    placeholders["athena_plan"].markdown(styled_status("📝", "Athena is building the development plan...", "working"), unsafe_allow_html=True)
                elif "DONE: Athena: Deconstructing" in cleaned_line:
                    placeholders["athena_plan"].markdown(styled_status("✅", "Athena has structured the development plan.", "success"), unsafe_allow_html=True)
                elif "START: Hephaestus: Writing" in cleaned_line:
                    key = f"hephaestus_code_{sprint_attempt}";
                    placeholders[key] = st.empty()
                    msg = "Hephaestus is writing the initial code..." if sprint_attempt == 1 else f"Hephaestus is correcting the code (Attempt {sprint_attempt})..."
                    placeholders[key].markdown(styled_status("⌨️", msg, "working"), unsafe_allow_html=True)
                elif "DONE: Hephaestus: Writing" in cleaned_line:
                    key = f"hephaestus_code_{sprint_attempt}";
                    placeholders[key].markdown(styled_status("✅", "Hephaestus has finished the code.", "success"), unsafe_allow_html=True)
                elif "START: Argus: Creating" in cleaned_line:
                    key = f"argus_test_{sprint_attempt}";
                    placeholders[key] = st.empty()
                    placeholders[key].markdown(styled_status("🔎", f"Argus is testing the code (Attempt {sprint_attempt})...", "working"), unsafe_allow_html=True)
                elif "DONE: Argus: Creating" in cleaned_line:
                    key = f"argus_test_{sprint_attempt}";
                    placeholders[key].markdown(styled_status("✅", "Argus confirmed all tests passed.", "success"), unsafe_allow_html=True)
                elif "FAIL: Argus: Tests failed" in cleaned_line:
                    key = f"argus_test_{sprint_attempt}";
                    placeholders[key].markdown(styled_status("⚠️", "Argus found bugs.", "warning"), unsafe_allow_html=True)
                elif "START: Athena: Analyzing" in cleaned_line:
                    key = f"athena_debug_{sprint_attempt}";
                    placeholders[key] = st.empty()
                    placeholders[key].markdown(styled_status("🤔", "Athena is analyzing the test failure...", "working"), unsafe_allow_html=True)
                elif "DONE: Athena: Analyzing" in cleaned_line:
                    key = f"athena_debug_{sprint_attempt}";
                    placeholders[key].markdown(styled_status("✅", "Athena has created a bug report.", "success"), unsafe_allow_html=True)
                    sprint_attempt += 1
                elif "START: Janus: Compiling" in cleaned_line:
                    placeholders["janus_report"] = st.empty()
                    placeholders["janus_report"].markdown(styled_status("📄", "Janus is now building the final report...", "working"), unsafe_allow_html=True)
                elif "DONE: Janus: Compiling" in cleaned_line or "---FINAL_REPORT---" in cleaned_line:
                    placeholders["janus_report"].markdown(styled_status("✅", "Janus has created the final report.", "success"), unsafe_allow_html=True)
            process.wait()
            st.session_state.pipeline_run_details["return_code"] = process.returncode
            st.session_state.pipeline_run_details["status"] = "completed"
            st.rerun()
        except Exception as e:
            st.error(f"A critical error occurred: {e}")
            st.session_state.pipeline_run_details["status"] = "error"

# --- Completed state: Final report display ---
elif status == "completed":
    final_output_str = "\n".join(st.session_state.pipeline_run_details.get("output", []))
    st.divider()
    st.subheader("3. Final Report")

    if "---ERROR---" in final_output_str or st.session_state.pipeline_run_details.get("return_code") != 0:
        st.error("Pipeline execution failed.")
    elif "---FINAL_REPORT---" in final_output_str:
        st.success("✔️ The pipeline has finished. See the report below.")
        _, report_content = final_output_str.split("---FINAL_REPORT---", 1)

        # Extract code and filename for download
        py_code_match = re.search(r"```python\n# (.*?\.py)\n(.*?)```", report_content, re.S)
        py_code = ""
        py_filename = "generated_code.py"
        if py_code_match:
            py_filename = py_code_match.group(1)
            py_code = py_code_match.group(2)

        # Create download buttons in columns
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="⬇️ Download Report (.md)",
                data=report_content.strip(),
                file_name="digital_forge_report.md",
                mime="text/markdown",
                use_container_width=True
            )
        with dl_col2:
            st.download_button(
                label=f"⬇️ Download Code ({py_filename})",
                data=py_code,
                file_name=py_filename,
                mime="text/x-python",
                use_container_width=True,
                disabled=not py_code
            )

        st.markdown(report_content.strip(),unsafe_allow_html=True)
    else:
        st.warning("Pipeline finished, but no final report was generated.")

    with st.expander("Show Full Execution Log"):
        st.code("\n".join(st.session_state.pipeline_run_details.get("output", [])),language="log")

# --- Footer ---
st.divider()
st.write("Powered by CrewAI • The Digital Forge")