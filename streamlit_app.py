# streamlit_app.py

import streamlit as st
import subprocess
import sys
import time

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
    <div class="status-box status-box-{status}">
        <div class="status-icon">{icon}</div>
        <div>{text}</div>
    </div>
    """

# --- App Header ---
st.title("🛠️ The Digital Forge")
st.caption("Your AI-Powered Software Development Crew")
st.write(
    "Welcome! Describe the function or feature you need, and the AI agent crew will build it. "
    "They will write the Python code, create tests to validate it, and even try to fix bugs they find along the way."
)
st.divider()

# --- Main Layout (Two Columns) ---
col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.subheader("1. Your Request")
    user_request = st.text_area(
        "**Describe the code you want the agents to write:**",
        height=200,
        placeholder="e.g., I need a Python function called `calculate_sum` in a file named `math_utils.py` that takes a list of numbers and returns their sum."
    )

    start_button = st.button("Start Forging", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Pipeline Status")
    status_area = st.container() # Use a container to group status updates

if start_button:
    if not user_request.strip():
        st.warning("Please enter a request before starting the forge.")
    else:
        # --- Execution Logic ---
        placeholders = {}
        sprint_attempt = 1
        
        # Clear previous status and prepare for new run
        status_area.empty()
        
        with status_area:
            log_expander = st.expander("▶️ Show Detailed Logs")
            log_placeholder = log_expander.empty()

        full_output = []
        
        try:
            # Launch the backend script
            process = subprocess.Popen(
                [sys.executable, "backend/main-deployment.py", user_request],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8'
            )

            # --- Stream and Parse Output ---
            for line in process.stdout:
                cleaned_line = line.strip()
                if not cleaned_line:
                    continue
                
                full_output.append(cleaned_line)
                log_placeholder.code("\n".join(full_output), language="log")

                # --- Update Status Placeholders Based on Backend Logs ---
                if "START: Janus: Clarifying" in cleaned_line:
                    with status_area:
                        placeholders["janus_brief"] = st.empty()
                    placeholders["janus_brief"].markdown(styled_status("🤔", "Janus is understanding the request...", "working"), unsafe_allow_html=True)
                elif "DONE: Janus: Clarifying" in cleaned_line:
                    placeholders["janus_brief"].markdown(styled_status("✅", "Janus has clarified the requirements.", "success"), unsafe_allow_html=True)

                elif "START: Athena: Deconstructing" in cleaned_line:
                    with status_area:
                        placeholders["athena_plan"] = st.empty()
                    placeholders["athena_plan"].markdown(styled_status("📝", "Athena is building the development plan...", "working"), unsafe_allow_html=True)
                elif "DONE: Athena: Deconstructing" in cleaned_line:
                    placeholders["athena_plan"].markdown(styled_status("✅", "Athena has structured the development plan.", "success"), unsafe_allow_html=True)

                elif "START: Hephaestus: Writing" in cleaned_line:
                    key = f"hephaestus_code_{sprint_attempt}"
                    with status_area:
                         placeholders[key] = st.empty()
                    message = "Hephaestus is writing the initial code..." if sprint_attempt == 1 else f"Hephaestus is correcting the code (Attempt {sprint_attempt})..."
                    placeholders[key].markdown(styled_status("⌨️", message, "working"), unsafe_allow_html=True)
                elif "DONE: Hephaestus: Writing" in cleaned_line:
                    key = f"hephaestus_code_{sprint_attempt}"
                    placeholders[key].markdown(styled_status("✅", "Hephaestus has finished the code.", "success"), unsafe_allow_html=True)

                elif "START: Argus: Creating" in cleaned_line:
                    key = f"argus_test_{sprint_attempt}"
                    with status_area:
                        placeholders[key] = st.empty()
                    placeholders[key].markdown(styled_status("🔎", f"Argus is testing the code (Attempt {sprint_attempt})...", "working"), unsafe_allow_html=True)
                elif "DONE: Argus: Creating" in cleaned_line:
                    key = f"argus_test_{sprint_attempt}"
                    placeholders[key].markdown(styled_status("✅", "Argus confirmed all tests passed.", "success"), unsafe_allow_html=True)
                
                elif "FAIL: Argus: Tests failed" in cleaned_line:
                    key = f"argus_test_{sprint_attempt}"
                    placeholders[key].markdown(styled_status("⚠️", "Argus found bugs.", "warning"), unsafe_allow_html=True)
                
                elif "START: Athena: Analyzing" in cleaned_line:
                    key = f"athena_debug_{sprint_attempt}"
                    with status_area:
                        placeholders[key] = st.empty()
                    placeholders[key].markdown(styled_status("🤔", "Athena is analyzing the test failure...", "working"), unsafe_allow_html=True)
                elif "DONE: Athena: Analyzing" in cleaned_line:
                    key = f"athena_debug_{sprint_attempt}"
                    placeholders[key].markdown(styled_status("✅", "Athena has created a bug report.", "success"), unsafe_allow_html=True)
                    sprint_attempt += 1

                elif "START: Janus: Compiling" in cleaned_line:
                    with status_area:
                        placeholders["janus_report"] = st.empty()
                    placeholders["janus_report"].markdown(styled_status("📄", "Janus is now building the final report...", "working"), unsafe_allow_html=True)

                time.sleep(0.01)

            process.wait()

        except Exception as e:
            st.error(f"A critical error occurred while launching the process: {e}")
            st.stop()

        # --- Final Report Display ---
        final_output_str = "\n".join(full_output)
        
        # Clear the status area and display the final report
        status_area.empty()

        with col2: # Re-draw the final report in the second column
            if "---ERROR---" in final_output_str or process.returncode != 0:
                st.error("Pipeline execution failed.")
            elif "---FINAL_REPORT---" in final_output_str:
                st.success("✔️ The final report is complete.")
                _, report_content = final_output_str.split("---FINAL_REPORT---", 1)
                st.markdown(report_content.strip(), unsafe_allow_html=True)
                st.download_button(
                    label="Download Report",
                    data=report_content.strip(),
                    file_name="digital_forge_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            else:
                st.warning("Pipeline finished, but no final report was generated.")
            
            # Show the detailed logs at the end
            with st.expander("Show Full Execution Log"):
                st.code("\n".join(full_output), language="log")

# --- Footer ---
st.divider()
st.write("Powered by CrewAI • The Digital Forge")