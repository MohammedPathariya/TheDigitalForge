# backend/main-deployment.py
# CLI entrypoint for Unit 734 - The Digital Forge (Production Ready)

import argparse
import json
import os
import re
import logging
import warnings
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process

# --- Configuration to Ensure Clean Execution ---
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
WORKSPACE_DIR = Path('backend/workspace')

class DevelopmentCrew:
    def __init__(self, user_request: str):
        self.user_request = user_request

    def _print_agent_output(self, agent_name: str, role: str, task_description: str, output: str):
        """Prints the output of an agent's task in a structured and readable format."""
        print("\n\n" + "─" * 80)
        print(f"👤 Agent: {agent_name} ({role})")
        print(f"📋 Task: {task_description}")
        print("─" * 80)
        match = re.search(r"Final Answer:(.*)", output, re.S)
        if match:
            clean_output = match.group(1).strip()
            clean_output = re.sub(r"```[a-zA-Z]*\n", "", clean_output)
            clean_output = clean_output.replace("```", "")
            print(clean_output.strip())
        else:
            print(output.strip())
        print("─" * 80)

    def run(self) -> str:
        """
        Runs the development crew process and returns the final client-facing report in Markdown.
        """
        # Phase 1: Planning & Scoping
        brief_crew = Crew(agents=[unit_734_crew['liaison']], tasks=[create_technical_brief], verbose=False)
        technical_brief = str(brief_crew.kickoff(inputs={'user_request': self.user_request}))
        self._print_agent_output("Janus", "Client Liaison", "Create a technical brief from the user request.", technical_brief)

        planning_crew = Crew(agents=[unit_734_crew['lead']], tasks=[define_development_plan], verbose=False)
        plan_output = planning_crew.kickoff(inputs={'technical_brief': technical_brief})
        try:
            clean_json = str(plan_output).strip().replace("```json", "").replace("```", "").strip()
            development_plan = json.loads(clean_json)
            self._print_agent_output("Athena", "Strategic Team Lead", "Create a detailed development plan.", json.dumps(development_plan, indent=2))
        except (json.JSONDecodeError, AttributeError) as e:
            error_md = f"# Error Generating Development Plan\nCould not parse development plan: {e}"
            return error_md

        # Phase 2: Development & Debugging
        test_results = ""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            print(f"\n🚀 Sprint Attempt {attempt}/{max_retries}...")
            developer_crew = Crew(agents=[unit_734_crew['developer']], tasks=[generate_python_code], verbose=False)
            code_output = str(developer_crew.kickoff(inputs=development_plan.copy()))
            self._print_agent_output("Hephaestus", "Principal Software Developer", "Write the Python code.", code_output)

            tester_crew = Crew(agents=[unit_734_crew['tester']], tasks=[generate_test_suite, execute_tests], process=Process.sequential, verbose=False)
            test_results = str(tester_crew.kickoff(inputs=development_plan.copy()))
            if "ALL TESTS PASSED" in test_results:
                self._print_agent_output("Argus", "Quality Assurance Tester", "Create and run the test suite.", test_results)
                break

            self._print_agent_output("Argus", "Quality Assurance Tester", "Create and run the test suite.", test_results)
            if attempt < max_retries:
                analysis_crew = Crew(agents=[unit_734_crew['lead']], tasks=[analyze_test_failure], verbose=False)
                bug_report = analysis_crew.kickoff(inputs={'test_failure_log': test_results, 'developer_task': development_plan['developer_task']})
                self._print_agent_output("Athena", "Strategic Team Lead", "Analyze test failures and create a bug report.", bug_report)
                development_plan['developer_task'] = str(bug_report)

        # Phase 3: Compiling Final Report
        return self._generate_final_report(technical_brief, test_results, development_plan)

    def _generate_final_report(self, brief: str, tests_output: str, dev_plan: dict) -> str:
        """
        Compiles the final report in Markdown and saves it to disk. Returns the Markdown content.
        """
        # Load final code and tests if available
        final_code = """
        Code could not be generated or finalized.
        """
        final_tests = """
        Tests could not be generated or finalized.
        """
        try:
            final_code = (WORKSPACE_DIR / dev_plan['file_name']).read_text()
        except Exception:
            pass
        try:
            final_tests = (WORKSPACE_DIR / dev_plan['test_file_name']).read_text()
        except Exception:
            pass

        # Build the report via the liaison agent
        reporting_crew = Crew(agents=[unit_734_crew['liaison']], tasks=[compile_final_report], verbose=False)
        raw_report = str(reporting_crew.kickoff(
            inputs={
                'technical_brief': brief,
                'final_code': final_code,
                'final_tests': final_tests,
                'test_results': tests_output,
                'final_outcome_summary': "All tests passed successfully." if "ALL TESTS PASSED" in tests_output else "Process completed with failing tests.",
                'file_name': dev_plan.get('file_name', 'N/A'),
                'test_file_name': dev_plan.get('test_file_name', 'N/A')
            }
        ))

        # Extract Markdown
        match = re.search(r"```markdown(.*)```", raw_report, re.S)
        markdown_content = match.group(1).strip() if match else raw_report

        # Save report files
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
    report_md = crew.run()
    print(report_md)