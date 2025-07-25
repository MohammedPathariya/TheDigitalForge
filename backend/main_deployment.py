# ======================
# ✅ UPDATED main_deployment.py
# ======================

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

# --- Determine project root and load .env ---
ROOT_DIR = Path(__file__).resolve().parent.parent
dotenv_path = ROOT_DIR / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}")

if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not set. Please add it to your .env file with 'OPENAI_API_KEY=YOUR_KEY'.")
    sys.exit(1)

warnings.filterwarnings("ignore")
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"
logging.getLogger('crewAI').setLevel(logging.CRITICAL)

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

WORKSPACE_DIR = ROOT_DIR / 'backend' / 'workspace'

class DevelopmentCrew:
    def __init__(self, user_request: str):
        self.user_request = user_request
        self.verbose = False

    def run(self) -> str:
        print("START: Janus: Clarifying requirements...")
        brief_crew = Crew(
            agents=[unit_734_crew['liaison']],
            tasks=[create_technical_brief],
            verbose=self.verbose
        )
        technical_brief = brief_crew.kickoff(inputs={'user_request': self.user_request})
        print("DONE: Janus: Clarifying requirements.")

        print("START: Athena: Deconstructing the brief...")
        planning_crew = Crew(
            agents=[unit_734_crew['lead']],
            tasks=[define_development_plan],
            verbose=self.verbose
        )
        plan_output = planning_crew.kickoff(inputs={'technical_brief': str(technical_brief)})
        clean_json = str(plan_output).strip().replace("```json", "").replace("```", "").strip()
        development_plan = json.loads(clean_json)
        print("DONE: Athena: Deconstructing the brief.")

        test_results = ""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            print(f"START: Hephaestus: Writing Python code (Attempt {attempt})...")
            developer_crew = Crew(agents=[unit_734_crew['developer']], tasks=[generate_python_code], verbose=self.verbose)
            developer_crew.kickoff(inputs=development_plan.copy())
            print(f"DONE: Hephaestus: Writing Python code (Attempt {attempt}).")

            print(f"START: Argus: Creating and running tests (Attempt {attempt})...")
            tester_crew = Crew(
                agents=[unit_734_crew['tester']],
                tasks=[generate_test_suite, execute_tests],
                process=Process.sequential,
                verbose=self.verbose
            )
            test_inputs = development_plan.copy()
            test_inputs["file_name"] = development_plan["file_name"]
            test_inputs["test_file_name"] = development_plan["test_file_name"]
            test_results = tester_crew.kickoff(inputs=test_inputs)

            if "ALL TESTS PASSED" in str(test_results):
                print(f"DONE: Argus: Creating and running tests (Attempt {attempt}).")
                break

            print("FAIL: Argus: Tests failed.")
            if attempt < max_retries:
                print("START: Athena: Analyzing test failure...")
                analysis_crew = Crew(agents=[unit_734_crew['lead']], tasks=[analyze_test_failure], verbose=self.verbose)
                bug_report = analysis_crew.kickoff(
                    inputs={'test_failure_log': str(test_results), 'developer_task': development_plan['developer_task']}
                )
                development_plan['developer_task'] = str(bug_report)
                print("DONE: Athena: Analyzing test failure.")
            else:
                print("FAIL: Reached max attempts. Proceeding to final report.")

        print("START: Janus: Compiling the final report...")
        return self._generate_final_report(
            brief=str(technical_brief),
            tests_output=str(test_results),
            dev_plan=development_plan
        )

    def _generate_final_report(self, brief: str, tests_output: str, dev_plan: dict) -> str:
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

        print("\n---FINAL_REPORT---")
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
