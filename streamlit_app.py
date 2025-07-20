import streamlit as st
import subprocess
import sys
import time
import re
import select

# --- Page Configuration ---
st.set_page_config(
    page_title="The Digital Forge",
    page_icon="🛠️",
    layout="wide"
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    .main .block-container { padding: 2rem 3rem; }
    .status-box { border: 1px solid #e0e0e0; border-left-width: 5px; border-radius: 5px;
        padding: 1rem; margin-bottom: 0.5rem; display: flex; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.3s ease-in-out; }
    .status-box-pending { border-left-color: #cccccc; }
    .status-box-working { border-left-color: #007bff; }
    .status-box-success { border-left-color: #28a745; }
    .status-box-warning { border-left-color: #ffc107; }
    .status-icon { font-size: 1.5rem; margin-right: 1rem; }
    .timeline-container { border: 1px solid #e0e0e0; border-radius: 5px;
        height: 300px; overflow-y: auto; padding: 1rem; background-color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# --- Helper for status updates ---
def styled_status(icon, text, status="pending"):
    return f'<div class="status-box status-box-{status}"><div class="status-icon">{icon}</div><div>{text}</div></div>'

# --- Event definitions ---
EVENT_DEFS = [
    ("START: Janus: Clarifying",     "janus_start",        "🤔", "Janus is understanding the request...",             "working"),
    ("DONE: Janus: Clarifying",      "janus_done",         "✅", "Janus has clarified the requirements.",             "success"),
    ("START: Athena: Deconstructing","athena_plan_start",  "📝", "Athena is building the development plan...",      "working"),
    ("DONE: Athena: Deconstructing", "athena_plan_done",   "✅", "Athena has structured the development plan.",     "success"),
    ("START: Hephaestus: Writing",    "hepha_start",        "⌨️", "Hephaestus is writing the code...",               "working"),
    ("DONE: Hephaestus: Writing",     "hepha_done",         "✅", "Hephaestus has finished the code.",               "success"),
    ("START: Argus: Creating",        "argus_start",        "🔎", "Argus is testing the code...",                   "working"),
    ("DONE: Argus: Creating",         "argus_done",         "✅", "Argus confirmed all tests passed.",              "success"),
    ("FAIL: Argus: Tests failed",     "argus_fail",         "⚠️", "Argus found bugs.",                              "warning"),
    ("START: Athena: Analyzing",      "athena_debug_start", "🔍", "Athena is analyzing the test failure...",        "working"),
    ("DONE: Athena: Analyzing",       "athena_debug_done",  "✅", "Athena has created a bug report.",               "success"),
    ("START: Hephaestus: Fixing",     "hepha_fix_start",    "🔧", "Hephaestus is applying bug fixes...",            "working"),
    ("DONE: Hephaestus: Fixing",      "hepha_fix_done",     "✅", "Hephaestus has applied bug fixes.",              "success"),
    ("START: Argus: Retesting",       "argus_retest_start", "🔄", "Argus is retesting the code...",                "working"),
    ("DONE: Argus: Retesting",        "argus_retest_done",  "✅", "Argus has confirmed all tests passed after fixes.","success"),
    ("START: Janus: Compiling",       "janus_report_start", "📝", "Janus is building the final report...",          "working"),
    ("---FINAL_REPORT---",            "janus_report_done",  "🏁", "Janus has created the final report.",             "success"),
]

# --- Initialize Session State ---
sess = st.session_state
sess.setdefault('pipeline_run_details', {})
sess.setdefault('printed_count', 0)
sess.setdefault('timeline', [])
sess.setdefault('seen_events', set())

# --- Header ---
st.title("🛠️ The Digital Forge")
st.caption("Your AI-Powered Software Development Crew")
st.write(
    "Welcome! Describe the code you need, and our AI crew will build and test it. "
    "For best results, please make your request as detailed as possible."
)
st.divider()

# --- Layout ---
col1, col2 = st.columns([1, 1.2], gap="large")
with col1:
    st.subheader("1. Your Request")
    user_request = st.text_area(
        "**Describe the code you want the agents to write:**",
        height=200,
        placeholder="e.g., I need a Python function called calculate_sum..."
    )
    start_button = st.button("Start Forging", type="primary", use_container_width=True)
    stop_button  = st.button("Stop Forging",  type="secondary", use_container_width=True)

with col2:
    st.subheader("2. Pipeline Status")
    elapsed_placeholder = st.empty()
    timeline_container = st.empty()

# --- Reset on stop ---
if stop_button:
    sess.pipeline_run_details.clear()
    sess.pop('start_time', None)
    sess.printed_count = 0
    sess.timeline.clear()
    sess.seen_events.clear()
    st.rerun()

# --- Start pipeline ---
if start_button:
    if not user_request.strip():
        st.warning("Please enter a request before starting the forge.")
    else:
        sess.start_time = time.time()
        sess.pipeline_run_details = {
            "output": [],
            "status": "running",
            "return_code": None,
            "user_request": user_request
        }
        sess.printed_count = 0
        sess.timeline.clear()
        sess.seen_events.clear()
        st.rerun()

status = sess.pipeline_run_details.get("status")

# --- Render timeline ---
def render_timeline():
    # redraw the entire timeline container
    html = "<div class='timeline-container'>"
    for icon, msg, state in sess.timeline:
        html += styled_status(icon, msg, state)
    html += "</div>"
    timeline_container.markdown(html, unsafe_allow_html=True)

# --- Append events once with delay ---
def render_new_events():
    for line in sess.pipeline_run_details.get('output', [])[sess.printed_count:]:
        for pattern, key, icon, msg, state in EVENT_DEFS:
            if pattern in line and key not in sess.seen_events:
                sess.timeline.append((icon, msg, state))
                sess.seen_events.add(key)
                render_timeline()
                time.sleep(1)
        sess.printed_count += 1

# --- Update timer and backlog ---
if 'start_time' in sess:
    elapsed_placeholder.markdown(f"**Elapsed Time:** {int(time.time() - sess.start_time)}s")
    render_new_events()

# --- Streaming loop ---
if status == "running":
    proc = subprocess.Popen([
        sys.executable, "backend/main-deployment.py", sess.pipeline_run_details.get("user_request", "")
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    stdout = proc.stdout
    while True:
        r, _, _ = select.select([stdout], [], [], 1)
        if r:
            line = stdout.readline()
            if not line:
                break
            sess.pipeline_run_details['output'].append(line)
        # update timer & events each second
        elapsed_placeholder.markdown(f"**Elapsed Time:** {int(time.time() - sess.start_time)}s")
        render_new_events()
        if 'janus_report_done' in sess.seen_events:
            proc.terminate()
            sess.pipeline_run_details['return_code'] = 0
            sess.pipeline_run_details['status'] = 'completed'
            break
        if proc.poll() is not None:
            sess.pipeline_run_details['return_code'] = proc.returncode
            sess.pipeline_run_details['status'] = 'completed'
            break
    proc.wait(timeout=1)
    st.rerun()

# --- Completed: simple success + logs ---
elif status == 'completed':
    render_timeline()
    elapsed_placeholder.markdown(f"**Elapsed Time:** {int(time.time() - sess.start_time)}s")
    st.divider()
    st.success("✔️ Pipeline completed successfully.")
    with st.expander("Show Full Execution Log"):
        log = "\n".join(sess.pipeline_run_details.get('output', []))
        st.code(log, language="log")

# --- Footer ---
st.divider()
st.write("Powered by CrewAI • The Digital Forge")