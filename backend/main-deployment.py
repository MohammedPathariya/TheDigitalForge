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

# --- Determine project root and load .env ---
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

# Define workspace path for file reading
WORKSPACE_DIR = ROOT_DIR / 'backend' / 'workspace'

class DevelopmentCrew:
    def __init__(self, user_request: str):
        self.user_request = user_request

    def _print_agent_output(self, agent_name: str, role: str, task_description: str, output):
        """Prints the output of an agent's task in a structured and readable format without assuming any specific format."""
        output_str = str(output)
        divider = "─" * 80
        print(f"\n\n{divider}")
        print(f"👤 Agent: {agent_name} ({role})")
        print(f"📋 Task: {task_description}")
        print(divider)
        # Simply print the full output to preserve all formats
        print(output_str)
        print(divider)

    def run(self) -> str:
        """
        Runs the development crew process and returns the final client-facing report in Markdown.
        """
        # Phase 1: Planning & Scoping
        brief_crew = Crew(
            agents=[unit_734_crew['liaison']],
            tasks=[create_technical_brief],
            verbose=True
        )
        try:
            technical_brief = brief_crew.kickoff(inputs={'user_request': self.user_request})
        except Exception as e:
            raise RuntimeError(f"Failed during technical brief generation: {e}")
        self._print_agent_output(
            "Janus", "Client Liaison",
            "Create a technical brief from the user request.",
            technical_brief
        )

        # Phase 1b: Development Plan
        planning_crew = Crew(
            agents=[unit_734_crew['lead']],
            tasks=[define_development_plan],
            verbose=True
        )
        try:
            plan_output = planning_crew.kickoff(inputs={'technical_brief': str(technical_brief)})
            clean_json = str(plan_output).strip().replace("```json", "").replace("```", "").strip()
            development_plan = json.loads(clean_json)
        except Exception as e:
            raise RuntimeError(f"Failed during development plan generation: {e}")
        self._print_agent_output(
            "Athena", "Strategic Team Lead",
            "Create a detailed development plan.",
            json.dumps(development_plan, indent=2)
        )

        # Phase 2: Development & Debugging
        test_results = None
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            print(f"\n🚀 Sprint Attempt {attempt}/{max_retries}...")
            # Code generation
            developer_crew = Crew(
                agents=[unit_734_crew['developer']],
                tasks=[generate_python_code],
                verbose=True
            )
            try:
                code_output = developer_crew.kickoff(inputs=development_plan.copy())
            except Exception as e:
                raise RuntimeError(f"Failed during code generation: {e}")
            self._print_agent_output(
                "Hephaestus", "Principal Software Developer",
                "Write the Python code.", code_output
            )

            # Test generation & execution
            tester_crew = Crew(
                agents=[unit_734_crew['tester']],
                tasks=[generate_test_suite, execute_tests],
                process=Process.sequential,
                verbose=True
            )
            try:
                test_results = tester_crew.kickoff(inputs=development_plan.copy())
            except Exception as e:
                raise RuntimeError(f"Failed during test execution: {e}")
            self._print_agent_output(
                "Argus", "Quality Assurance Tester",
                "Create and run the test suite.", test_results
            )
            if isinstance(test_results, str) and "ALL TESTS PASSED" in test_results:
                break

            # If tests failed, analyze and retry
            if attempt < max_retries:
                analysis_crew = Crew(
                    agents=[unit_734_crew['lead']],
                    tasks=[analyze_test_failure],
                    verbose=True
                )
                bug_report = analysis_crew.kickoff(
                    inputs={
                        'test_failure_log': str(test_results),
                        'developer_task': development_plan['developer_task']
                    }
                )
                self._print_agent_output(
                    "Athena", "Strategic Team Lead",
                    "Analyze test failures and create a bug report.", bug_report
                )
                development_plan['developer_task'] = str(bug_report)

        # Phase 3: Compiling Final Report
        return self._generate_final_report(
            brief=str(technical_brief),
            tests_output=str(test_results),
            dev_plan=development_plan
        )

    def _generate_final_report(self, brief: str, tests_output: str, dev_plan: dict) -> str:
        """
        Compiles the final report in Markdown and saves it to disk. Returns the Markdown content.
        """
        # Read final code and tests
        try:
            final_code = (WORKSPACE_DIR / dev_plan['file_name']).read_text()
        except Exception:
            final_code = "Code could not be generated or finalized."
        try:
            final_tests = (WORKSPACE_DIR / dev_plan['test_file_name']).read_text()
        except Exception:
            final_tests = "Tests could not be generated or finalized."

        # Compile report
        reporting_crew = Crew(
            agents=[unit_734_crew['liaison']],
            tasks=[compile_final_report],
            verbose=True
        )
        raw_report = reporting_crew.kickoff(
            inputs={
                'technical_brief': brief,
                'final_code': final_code,
                'final_tests': final_tests,
                'test_results': tests_output,
                'final_outcome_summary': (
                    "All tests passed successfully." if "ALL TESTS PASSED" in tests_output else "Process completed with failing tests."
                ),
                'file_name': dev_plan.get('file_name', 'N/A'),
                'test_file_name': dev_plan.get('test_file_name', 'N/A')
            }
        )
        raw_report_str = str(raw_report)
        match = re.search(r"```markdown(.*)```", raw_report_str, re.S)
        markdown_content = match.group(1).strip() if match else raw_report_str

        # Save report
        save_report.func(file_name_stem="Final_Report", markdown_content=markdown_content)

        return markdown_content


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Digital Forge pipeline")
    parser.add_argument(
        "request",
        type=str,
        help="The user request to turn into code+tests",
    )
    args = parser.parse_args()
    crew = DevelopmentCrew(args.request)
    try:
        report_md = crew.run()
        print(report_md)
    except Exception:
        print("Error during pipeline execution:")
        traceback.print_exc()
        sys.exit(1)
