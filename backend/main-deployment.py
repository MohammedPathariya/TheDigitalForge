# backend/main-deployment.py
# CLI entrypoint for Unit 734 - The Digital Forge (Production Ready)

import argparse
import json
import os
import re
import sys
import traceback
import logging
import warnings
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process

# --- MOVED: Determine project root and load .env ---
ROOT_DIR = Path(__file__).resolve().parent.parent
dotenv_path = ROOT_DIR / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}")

# Ensure OPENAI_API_KEY is set
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not set. Please add it to your .env file with 'OPENAI_API_KEY=YOUR_KEY'.")
    sys.exit(1)

# Suppress warnings and telemetry
warnings.filterwarnings("ignore")
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"
logging.getLogger('crewAI').setLevel(logging.CRITICAL)

# Correctly import the agent dictionary and tasks
from agents import unit_734_crew
from tasks import (
    create_technical_brief,
    define_development_plan,
    generate_python_code,
    generate_test_suite,
    execute_tests,
    analyze_test_failure,
    compile_final_report
)
from tools import save_report

# --- This will now work correctly ---
WORKSPACE_DIR = ROOT_DIR / 'workspace'

class DevelopmentCrew:
    def __init__(self, user_request: str):
        self.user_request = user_request
        self.verbose = False # Set to False for cleaner CLI logs

    def run(self) -> str:
        """
        Runs the full development and testing pipeline.
        It will always generate a final report after the process is complete, regardless of test outcomes.
        """
        # Phase 1: Planning
        print("👤 [Janus] Creating technical brief...")
        brief_crew = Crew(
            agents=[unit_734_crew['liaison']],
            tasks=[create_technical_brief],
            verbose=self.verbose
        )
        technical_brief = brief_crew.kickoff(inputs={'user_request': self.user_request})
        print("✅ [Janus] Technical brief created.")

        print("\n👤 [Athena] Creating development plan...")
        planning_crew = Crew(
            agents=[unit_734_crew['lead']],
            tasks=[define_development_plan],
            verbose=self.verbose
        )
        plan_output = planning_crew.kickoff(inputs={'technical_brief': str(technical_brief)})
        clean_json = str(plan_output).strip().replace("```json", "").replace("```", "").strip()
        development_plan = json.loads(clean_json)
        print("✅ [Athena] Development plan created.")

        # Phase 2: Development & Debugging Loop
        test_results = ""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            print(f"\n🚀 Sprint Attempt {attempt}/{max_retries}...")
            
            print("👤 [Hephaestus] Writing Python code...")
            developer_crew = Crew(agents=[unit_734_crew['developer']], tasks=[generate_python_code], verbose=self.verbose)
            developer_crew.kickoff(inputs=development_plan.copy())
            print("✅ [Hephaestus] Code saved to workspace.")

            print("👤 [Argus] Writing and running tests...")
            tester_crew = Crew(
                agents=[unit_734_crew['tester']],
                tasks=[generate_test_suite, execute_tests],
                process=Process.sequential,
                verbose=self.verbose
            )
            test_results = tester_crew.kickoff(inputs=development_plan.copy())
            
            if "ALL TESTS PASSED" in str(test_results):
                print("✅ [Argus] All tests passed!")
                break  # Exit the loop on success
            
            print(f"❌ [Argus] Tests failed on attempt {attempt}.")
            if attempt < max_retries:
                print("👤 [Athena] Analyzing failure for next sprint...")
                analysis_crew = Crew(agents=[unit_734_crew['lead']], tasks=[analyze_test_failure], verbose=self.verbose)
                bug_report = analysis_crew.kickoff(
                    inputs={'test_failure_log': str(test_results), 'developer_task': development_plan['developer_task']}
                )
                development_plan['developer_task'] = str(bug_report)
                print("✅ [Athena] New task created for developer.")
            else:
                print("⚠️ Reached max attempts. Proceeding to final report.")

        # Phase 3: Final Reporting (Always runs)
        print("\n✅ Development cycles complete. Compiling final report...")
        return self._generate_final_report(
            brief=str(technical_brief),
            tests_output=str(test_results),
            dev_plan=development_plan
        )

    def _generate_final_report(self, brief: str, tests_output: str, dev_plan: dict) -> str:
        """
        Compiles and saves the final report, indicating the final outcome.
        """
        final_outcome_summary = (
            "All tests passed successfully." if "ALL TESTS PASSED" in tests_output 
            else "Process completed with failing tests. The code below is the latest iteration and may not be fully functional."
        )

        try:
            final_code = (WORKSPACE_DIR / dev_plan['file_name']).read_text()
        except Exception:
            final_code = "Error: Code could not be read from the workspace."
        try:
            final_tests = (WORKSPACE_DIR / dev_plan['test_file_name']).read_text()
        except Exception:
            final_tests = "Error: Tests could not be read from the workspace."

        reporting_crew = Crew(
            agents=[unit_734_crew['liaison']],
            tasks=[compile_final_report],
            verbose=self.verbose
        )
        
        # Pass all necessary context to the reporting task
        raw_report = reporting_crew.kickoff(
            inputs={
                'technical_brief': brief,
                'final_code': final_code,
                'final_tests': final_tests,
                'test_results': tests_output,
                'final_outcome_summary': final_outcome_summary,
                'file_name': dev_plan.get('file_name', 'N/A'),
                'test_file_name': dev_plan.get('test_file_name', 'N/A')
            }
        )
        
        print("\n---FINAL_REPORT---") # Separator for the frontend
        
        raw_report_str = str(raw_report)
        match = re.search(r"```markdown(.*)```", raw_report_str, re.S)
        markdown_content = match.group(1).strip() if match else raw_report_str
        
        save_report.func(file_name_stem="Final_Report", markdown_content=markdown_content)
        return markdown_content


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Digital Forge pipeline")
    parser.add_argument("request", type=str, help="The user request to turn into code+tests")
    args = parser.parse_args()
    crew = DevelopmentCrew(args.request)
    try:
        final_report = crew.run()
        print(final_report)
    except Exception as e:
        print("\n---ERROR---")
        print("A critical error occurred during the pipeline execution:")
        traceback.print_exc()
        sys.exit(1)