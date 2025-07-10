# streamlit_app.py

import streamlit as st
import subprocess
import sys

# Configuration
st.set_page_config(page_title="Digital Forge", layout="wide")

# App header
st.title("🛠️ The Digital Forge")
st.write("Enter a description of the code you want generated, and let the Digital Forge pipeline do the rest.")

# Input area
user_request = st.text_area(
    label="Describe your feature or function:",
    height=200,
    placeholder="E.g., 'I need a function to calculate the factorial of a number...'"
)

if st.button("Generate Code & Tests"):
    if not user_request.strip():
        st.warning("Please enter a request above.")
    else:
        # Placeholder for the entire output area
        results_area = st.empty()
        
        # Use a single container for live logs
        log_container = results_area.container()
        log_box = log_container.expander("▶️ Show Pipeline Logs", expanded=True)
        log_text = log_box.empty()
        
        output_lines = []
        
        try:
            # Launch subprocess with line buffering
            process = subprocess.Popen(
                [sys.executable, "backend/main-deployment.py", user_request],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8'
            )
            
            # Stream and accumulate logs
            for raw_line in process.stdout:
                line = raw_line.rstrip()
                output_lines.append(line)
                # Update the log box with full history, filtering out the separator
                current_log_content = "\n".join(
                    [l for l in output_lines if "---FINAL_REPORT---" not in l and "---ERROR---" not in l]
                )
                log_text.code(current_log_content)
            
            process.wait()

        except Exception as e:
            st.error(f"An error occurred while launching the process: {e}")
            st.stop()

        # Process the final output
        full_output = "\n".join(output_lines)

        if "---ERROR---" in full_output or process.returncode != 0:
            log_content, error_content = full_output.split("---ERROR---" if "---ERROR---" in full_output else "\n", 1)
            results_area.error("Pipeline execution failed. See logs for details.")
            with st.expander("Error Logs", expanded=True):
                st.text(error_content.strip())
        
        elif "---FINAL_REPORT---" in full_output:
            log_content, report_content = full_output.split("---FINAL_REPORT---", 1)
            
            # Clear the old results area and replace it with the final report
            results_area.empty()
            st.success("Pipeline completed successfully!")
            st.markdown(report_content.strip(), unsafe_allow_html=True)
            with st.expander("Show Final Pipeline Logs"):
                st.code(log_content.strip())
        else:
             results_area.warning("Pipeline finished, but no final report was generated. See logs for details.")
             with st.expander("Show Final Pipeline Logs", expanded=True):
                 st.code(full_output)


# Footer
st.markdown("---")
st.write("Powered by CrewAI • Digital Forge")