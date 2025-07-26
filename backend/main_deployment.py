# backend/main_deployment.py

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

# --- Load .env and configure logging/telemetry ---
ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR.parent / '.env')
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not set.")
    sys.exit(1)

warnings.filterwarnings("ignore")
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"
logging.getLogger('crewAI').setLevel(logging.CRITICAL)

# --- Import agents & tasks ---
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
from tools import IN_MEMORY_WORKSPACE, clear_workspace

class DevelopmentCrew:
    def __init__(self, user_request: str):
        self.user_request = user_request

    def run(self) -> str:
        clear_workspace()
        try:
            # Phase 1: Planning
            brief_crew = Crew(agents=[unit_734_crew['liaison']], tasks=[create_technical_brief], verbose=False)
            technical_brief = str(brief_crew.kickoff(inputs={'user_request': self.user_request}))

            plan_crew = Crew(agents=[unit_734_crew['lead']], tasks=[define_development_plan], verbose=False)
            plan_raw = str(plan_crew.kickoff(inputs={'technical_brief': technical_brief}))
            plan_json = plan_raw.strip().replace("```json", "").replace("```", "").strip()
            plan = json.loads(plan_json)

            file_name = plan['file_name']
            test_file_name = plan['test_file_name']
            developer_task = plan['developer_task']
            tester_task = plan['tester_task']

            # Phase 2: Development & Debugging Loop
            test_results = ""
            for attempt in range(1, 4):
                dev_crew = Crew(agents=[unit_734_crew['developer']], tasks=[generate_python_code], verbose=False)
                dev_crew.kickoff(inputs={'developer_task': developer_task, 'file_name': file_name})

                test_crew = Crew(
                    agents=[unit_734_crew['tester']],
                    tasks=[generate_test_suite, execute_tests],
                    process=Process.sequential,
                    verbose=False
                )
                test_results = str(test_crew.kickoff(inputs={
                    'tester_task': tester_task,
                    'file_name': file_name,
                    'test_file_name': test_file_name
                }))

                if "ALL TESTS PASSED" in test_results:
                    break

                if attempt < 3:
                    analysis_crew = Crew(agents=[unit_734_crew['lead']], tasks=[analyze_test_failure], verbose=False)
                    bug_raw = str(analysis_crew.kickoff(inputs={
                        'developer_task': plan['developer_task'],
                        'test_failure_log': test_results,
                        'file_name': file_name,
                        'test_file_name': test_file_name
                    }))
                    bug_json = bug_raw.strip().replace("```json", "").replace("```", "").strip()
                    bug_report = json.loads(bug_json)

                    # --- CRITICAL ORCHESTRATION FIX ---
                    # Check Athena's diagnosis and route the next task to the correct agent.
                    if bug_report.get('file_to_fix') == file_name:
                        # If the code is buggy, update the developer's task for the next loop.
                        developer_task = bug_report['next_task']
                    elif bug_report.get('file_to_fix') == test_file_name:
                        # If the test is buggy, update the tester's task for the next loop.
                        tester_task = bug_report['next_task']
                    else:
                        # Fallback if the file_to_fix is unclear, assume code error.
                        developer_task = bug_report['next_task']

            # Phase 3: Final Reporting
            return self._generate_final_report(technical_brief, test_results, plan)

        except Exception:
            traceback.print_exc()
            return "❌ A critical error occurred during the pipeline execution."

    def _generate_final_report(self, brief: str, tests_output: str, dev_plan: dict) -> str:
        file_name = dev_plan.get('file_name', 'unknown.py')
        test_file_name = dev_plan.get('test_file_name', 'test_unknown.py')
        
        final_code = IN_MEMORY_WORKSPACE.get(file_name, f"Error: Code for {file_name} not found in memory.")
        final_tests = IN_MEMORY_WORKSPACE.get(test_file_name, f"Error: Tests for {test_file_name} not found in memory.")

        outcome = "All tests passed successfully." if "ALL TESTS PASSED" in tests_output else "Process completed with failing tests."

        report_crew = Crew(agents=[unit_734_crew['liaison']], tasks=[compile_final_report], verbose=False)
        report_raw = report_crew.kickoff(inputs={
            'technical_brief': brief,
            'final_code': final_code,
            'final_tests': final_tests,
            'test_results': tests_output,
            'file_name': file_name,
            'test_file_name': test_file_name,
            'final_outcome_summary': outcome
        })
        report_str = str(report_raw)
        
        match = re.search(r"```markdown(.*)```", report_str, re.S)
        return match.group(1).strip() if match else report_str

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Digital Forge pipeline")
    parser.add_argument("request", type=str, help="The user request")
    args = parser.parse_args()
    crew = DevelopmentCrew(args.request)
    print(crew.run())
