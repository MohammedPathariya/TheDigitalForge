# streamlit_app.py

import streamlit as st
import subprocess
import sys
import re
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="The Digital Forge",
    page_icon="🛠️",
    layout="wide"
)

# --- App Header ---
st.title("🛠️ The Digital Forge")
st.write(
    "Welcome! Describe the function or feature you need, and the AI agent crew will build it. "
    "They will write the Python code, create tests to validate it, and even try to fix bugs they find along the way."
)

# --- Input Area ---
user_request = st.text_area(
    "**Enter your request below:**",
    height=150,
    placeholder="e.g., I need a function that takes a list of numbers and returns the sum."
)

if st.button("Start Forging", type="primary"):
    if not user_request.strip():
        st.warning("Please enter a request before starting the forge.")
    else:
        # --- Execution Area ---
        st.markdown("---")
        st.subheader("Forge Pipeline Status")
        
        # --- Dynamic Status Placeholders ---
        placeholders = {}
        sprint_attempt = 1

        log_expander = st.expander("▶️ Show Detailed Logs")
        log_placeholder = log_expander.empty()

        full_output = []
        
        try:
            # Launch the backend script as a subprocess
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
                log_placeholder.code("\n".join(full_output))

                # --- Update Status Placeholders Based on Backend Logs ---
                if line.startswith("START:"):
                    if "Janus: Clarifying" in line:
                        placeholders["janus_brief"] = st.empty()
                        placeholders["janus_brief"].info("🤔 Janus is understanding the request...")
                    elif "Athena: Deconstructing" in line:
                        placeholders["athena_plan"] = st.empty()
                        placeholders["athena_plan"].info("📝 Athena is building the development plan...")
                    elif "Hephaestus: Writing" in line:
                        # Use a unique key for each sprint attempt
                        key = f"hephaestus_code_{sprint_attempt}"
                        placeholders[key] = st.empty()
                        message = "⌨️ Hephaestus is writing the code..." if sprint_attempt == 1 else f"⌨️ Hephaestus is correcting the code (Attempt {sprint_attempt})..."
                        placeholders[key].info(message)
                    elif "Argus: Creating" in line:
                        key = f"argus_test_{sprint_attempt}"
                        placeholders[key] = st.empty()
                        placeholders[key].info(f"🔎 Argus is testing the code (Attempt {sprint_attempt})...")
                    elif "Athena: Analyzing" in line:
                        key = f"athena_debug_{sprint_attempt}"
                        placeholders[key] = st.empty()
                        placeholders[key].info("🤔 Athena is analyzing the test failure...")
                    elif "Janus: Compiling" in line:
                        placeholders["janus_report"] = st.empty()
                        placeholders["janus_report"].info("📄 Janus is building the final report...")

                elif line.startswith("DONE:"):
                    if "Janus: Clarifying" in line:
                        placeholders["janus_brief"].success("✔️ Janus has clarified the requirements.")
                    elif "Athena: Deconstructing" in line:
                        placeholders["athena_plan"].success("✔️ Athena has structured the development plan.")
                    elif "Hephaestus: Writing" in line:
                        key = f"hephaestus_code_{sprint_attempt}"
                        placeholders[key].success("✔️ Hephaestus has finished the code.")
                    elif "Argus: Creating" in line:
                        key = f"argus_test_{sprint_attempt}"
                        placeholders[key].success("✔️ Argus confirmed all tests passed.")
                    elif "Athena: Analyzing" in line:
                        key = f"athena_debug_{sprint_attempt}"
                        placeholders[key].success("✔️ Athena has created a bug report.")
                
                elif line.startswith("FAIL:"):
                    if "Argus: Tests failed" in line:
                        key = f"argus_test_{sprint_attempt}"
                        placeholders[key].warning("⚠️ Argus found bugs.")
                        sprint_attempt += 1 # Increment for the next loop

                time.sleep(0.01)

            process.wait()

        except Exception as e:
            st.error(f"A critical error occurred while launching the process: {e}")
            st.stop()

        # --- Final Report Display ---
        final_output_str = "\n".join(full_output)
        
        # Clear the status placeholders before showing the final report
        for ph in placeholders.values():
            ph.empty()

        if "---ERROR---" in final_output_str or process.returncode != 0:
            st.error("Pipeline execution failed.")
        
        elif "---FINAL_REPORT---" in final_output_str:
            st.success("✔️ The final report is complete.")
            _, report_content = final_output_str.split("---FINAL_REPORT---", 1)
            st.markdown("---")
            st.subheader("Final Report")
            st.markdown(report_content.strip(), unsafe_allow_html=True)
            st.download_button(
                label="Download Report",
                data=report_content.strip(),
                file_name="digital_forge_report.md",
                mime="text/markdown"
            )
        else:
            st.warning("Pipeline finished, but no final report was generated.")

# --- Footer ---
st.markdown("---")
st.write("Powered by CrewAI • The Digital Forge")