# streamlit_app.py

import streamlit as st
import requests
import time

# --- Config ---
BACKEND_URL = "https://thedigitalforge-backend.onrender.com/run"

# --- Page Configuration ---
st.set_page_config(
    page_title="The Digital Forge",
    page_icon="🛠️",
    layout="wide"
)

# --- Custom CSS ---
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
</style>
""", unsafe_allow_html=True)

# --- Initialize Session ---
sess = st.session_state
sess.setdefault("status", None)
sess.setdefault("start_time", None)
sess.setdefault("pipeline_output", "")
sess.setdefault("user_request", "")

# --- Header UI ---
st.title("🛠️ The Digital Forge")
st.caption("Your AI-Powered Software Development Crew")
st.write(
    "Welcome! Describe the code you need, and our AI agents will build and test it for you. "
    "The more specific your request, the better the results!"
)
st.divider()

# --- Layout ---
col1, col2 = st.columns([1, 1.2], gap="large")
with col1:
    st.subheader("1. Your Request")
    user_input = st.text_area(
        "**Describe the code you want built:**",
        height=200,
        placeholder="e.g., I need a Python script that fetches weather data and plots it."
    )
    start_button = st.button("Start Forging", type="primary", use_container_width=True)
    stop_button = st.button("Reset", type="secondary", use_container_width=True)

with col2:
    st.subheader("2. Pipeline Progress")
    timer_placeholder = st.empty()
    report_placeholder = st.empty()

# --- Timer Display ---
if sess.status == "running" and sess.start_time:
    elapsed = int(time.time() - sess.start_time)
    timer_placeholder.markdown(f"⏱ **Elapsed Time:** {elapsed}s")

# --- Reset Pipeline ---
if stop_button:
    sess.status = None
    sess.pipeline_output = ""
    sess.user_request = ""
    sess.start_time = None
    st.rerun()

# --- Start Pipeline ---
if start_button:
    if not user_input.strip():
        st.warning("Please enter a request before starting.")
    else:
        sess.start_time = time.time()
        sess.status = "running"
        sess.user_request = user_input.strip()
        sess.pipeline_output = ""
        st.rerun()

# --- Handle Backend Request ---
if sess.status == "running" and sess.user_request:
    with st.spinner("🔄 The crew is working on your request..."):
        try:
            response = requests.post(BACKEND_URL, json={"request": sess.user_request}, timeout=600)
            if response.status_code == 200:
                sess.pipeline_output = response.json().get("report", "")
                sess.status = "completed"
            else:
                sess.pipeline_output = f"❌ Backend Error ({response.status_code}): {response.text}"
                sess.status = "error"
        except Exception as e:
            sess.pipeline_output = f"❌ Request failed: {str(e)}"
            sess.status = "error"
    st.rerun()

# --- Display Final Report or Errors ---
if sess.status == "completed":
    elapsed = int(time.time() - sess.start_time)
    timer_placeholder.markdown(f"⏱ **Elapsed Time:** {elapsed}s")
    st.success("✔️ Pipeline completed successfully.")
    report_placeholder.markdown(sess.pipeline_output, unsafe_allow_html=True)

elif sess.status == "error":
    st.error("❌ Something went wrong during execution.")
    report_placeholder.code(sess.pipeline_output)

# --- Footer ---
st.divider()
st.markdown("Made with ❤️ using CrewAI • Powered by The Digital Forge")