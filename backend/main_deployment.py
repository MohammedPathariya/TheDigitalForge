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

# Load environment and suppress logs
ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR.parent / '.env')
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not set.")
    sys.exit(1)
warnings.filterwarnings("ignore")
logging.getLogger('crewAI').setLevel(logging.CRITICAL)

# Import your agents and tasks
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

# Ensure an in-memory workspace exists for this request
WORKSPACE_DIR = ROOT_DIR / 'workspace'
WORKSPACE_DIR.mkdir(exist_ok=True)

class DevelopmentCrew:
    def __init__(self, user_request: str):
        self.user_request = user_request

    def run(self) -> str:
        try:
            # --- Phase 1: Technical Brief ---
            brief_crew = Crew(
                agents=[unit_734_crew['liaison']],
                tasks=[create_technical_brief],
                verbose=False
            )
            technical_brief = str(brief_crew.kickoff(
                inputs={'user_request': self.user_request}
            ))

            # --- Phase 2: Development Plan ---
            plan_crew = Crew(
                agents=[unit_734_crew['lead']],
                tasks=[define_development_plan],
                verbose=False
            )
            plan_raw = str(plan_crew.kickoff(
                inputs={'technical_brief': technical_brief}
            ))
            # strip markdown fences if any
            plan_json = plan_raw.strip().replace("```json", "").replace("```", "").strip()
            plan = json.loads(plan_json)

            file_name       = plan['file_name']
            test_file_name  = plan['test_file_name']
            developer_task  = plan['developer_task']
            tester_task     = plan['tester_task']

            # --- Phase 3: Code + Test Loop ---
            test_results = ""
            for attempt in range(1, 4):
                # 3a. Generate code
                dev_crew = Crew(
                    agents=[unit_734_crew['developer']],
                    tasks=[generate_python_code],
                    verbose=False
                )
                dev_crew.kickoff(inputs={
                    'developer_task': developer_task,
                    'file_name': file_name
                })

                # 3b. Generate & execute tests
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

                # 3c. If tests failed and we have retries left, analyze and update task
                if attempt < 3:
                    analysis_crew = Crew(
                        agents=[unit_734_crew['lead']],
                        tasks=[analyze_test_failure],
                        verbose=False
                    )
                    bug_report_raw = str(analysis_crew.kickoff(inputs={
                        'developer_task': developer_task,
                        'test_failure_log': test_results,
                        'file_name': file_name,
                        'test_file_name': test_file_name
                    }))
                    # extract JSON from fences
                    bug_json = bug_report_raw.strip().replace("```json", "").replace("```", "").strip()
                    bug = json.loads(bug_json)

                    # update next task
                    if bug['file_to_fix'] == file_name:
                        developer_task = bug['next_task']
                    else:
                        tester_task = bug['next_task']
                # else--no retries, break
            # end loop

            # --- Phase 4: Prepare Final Code & Tests for Report ---
            code_path = WORKSPACE_DIR / file_name
            try:
                final_code = code_path.read_text()
            except Exception:
                final_code = f"Error: Could not read code file {file_name}."

            tests_path = WORKSPACE_DIR / test_file_name
            try:
                final_tests = tests_path.read_text()
            except Exception:
                final_tests = f"Error: Could not read test file {test_file_name}."

            outcome = (
                "All tests passed successfully."
                if "ALL TESTS PASSED" in test_results
                else "Process completed with failing tests."
            )

            # --- Phase 5: Compile Final Report ---
            report_crew = Crew(
                agents=[unit_734_crew['liaison']],
                tasks=[compile_final_report],
                verbose=False
            )
            report_raw = report_crew.kickoff(inputs={
                'technical_brief': technical_brief,
                'final_code': final_code,
                'final_tests': final_tests,
                'test_results': test_results,
                'file_name': file_name,
                'test_file_name': test_file_name,
                'final_outcome_summary': outcome
            })
            report_str = str(report_raw)

            # Extract markdown inside fences, if present
            match = re.search(r"```markdown(.*)```", report_str, re.S)
            if match:
                return match.group(1).strip()
            return report_str

        except Exception:
            traceback.print_exc()
            return "❌ A critical error occurred during the pipeline."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Digital Forge pipeline")
    parser.add_argument("request", type=str, help="The user request")
    args = parser.parse_args()

    crew = DevelopmentCrew(args.request)
    output = crew.run()
    print(output)