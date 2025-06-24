# backend/main.py
# CLI entrypoint for Unit 734 - The Digital Forge (Production Ready)

import json
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process
import warnings
import os
import sys
import re
import logging

# --- Configuration to Ensure Clean Execution ---
# Suppress all warnings to keep the output pristine.
warnings.filterwarnings("ignore")
# Disable crewAI's telemetry to prevent connection timeout errors.
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"
# Silence the crewAI logger to remove the raw agent "thinking" logs.
logging.getLogger('crewAI').setLevel(logging.CRITICAL)


# Correctly import the agent dictionary and individual tasks
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
# Import the correct tool name 'save_report'
from tools import save_report

# Load environment variables
load_dotenv()

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
        # Find and print only the final answer part of the output, cleaning it up
        match = re.search(r"Final Answer:(.*)", output, re.S)
        if match:
            clean_output = match.group(1).strip()
            # Further clean up markdown code blocks if they exist
            clean_output = re.sub(r"```[a-zA-Z]*\n", "", clean_output)
            clean_output = clean_output.replace("```", "")
            print(clean_output.strip())
        else:
            print(output.strip()) # Fallback for simple outputs
        print("─" * 80)

    def run(self):
        """
        Runs the development crew process with production-ready logging, 
        ensuring a final report is always generated.
        """
        self.agents = unit_734_crew
        self.tasks = {
            'brief': create_technical_brief,
            'plan': define_development_plan,
            'develop': generate_python_code,
            'test_suite': generate_test_suite,
            'execute_tests': execute_tests,
            'analyze_failure': analyze_test_failure,
            'final_report': compile_final_report,
        }

        print("\n--- [Phase 1/3] Planning & Scoping ---")
        
        brief_crew = Crew(agents=[self.agents['liaison']], tasks=[self.tasks['brief']], verbose=False)
        technical_brief = str(brief_crew.kickoff(inputs={'user_request': self.user_request}))
        self._print_agent_output("Janus", "Client Liaison", "Create a technical brief from the user request.", technical_brief)

        planning_crew = Crew(agents=[self.agents['lead']], tasks=[self.tasks['plan']], verbose=False)
        plan_output = planning_crew.kickoff(inputs={'technical_brief': technical_brief})
        
        try:
            clean_json_string = str(plan_output).strip().replace("```json", "").replace("```", "").strip()
            development_plan = json.loads(clean_json_string)
            self._print_agent_output("Athena", "Strategic Team Lead", "Create a detailed development plan.", json.dumps(development_plan, indent=2))
        except (json.JSONDecodeError, AttributeError) as e:
            error_message = f"❌ Error: Could not parse the development plan. Aborting. Error: {e}"
            print(error_message)
            self._generate_final_report(technical_brief, "Planning failed.", "No code generated.", "No tests generated.", {})
            return
        
        print("\n--- [Phase 2/3] Development & Debugging ---")
        max_retries = 3
        test_results = ""
        
        for attempt in range(1, max_retries + 1):
            print(f"\n🚀 Sprint Attempt {attempt}/{max_retries}...")
            
            developer_crew = Crew(agents=[self.agents['developer']], tasks=[self.tasks['develop']], verbose=False)
            code_output = str(developer_crew.kickoff(inputs=development_plan.copy()))
            self._print_agent_output("Hephaestus", "Principal Software Developer", "Write the Python code.", f"✅ Code written to file: {code_output}")

            tester_crew = Crew(agents=[self.agents['tester']], tasks=[self.tasks['test_suite'], self.tasks['execute_tests']], process=Process.sequential, verbose=False)
            test_results = str(tester_crew.kickoff(inputs=development_plan.copy()))
            
            if "ALL TESTS PASSED" in test_results:
                self._print_agent_output("Argus", "Quality Assurance Tester", "Create and run the test suite.", f"✅ All Tests Passed!")
                break
            
            self._print_agent_output("Argus", "Quality Assurance Tester", "Create and run the test suite.", f"⚠️  Tests Failed.\n\n{test_results}")
            if attempt < max_retries:
                analysis_crew = Crew(agents=[self.agents['lead']], tasks=[self.tasks['analyze_failure']], verbose=False)
                bug_report = analysis_crew.kickoff(inputs={'test_failure_log': test_results, 'developer_task': development_plan['developer_task']})
                self._print_agent_output("Athena", "Strategic Team Lead", "Analyze test failures and create a bug report.", f"📝 Bug Report for next sprint:\n\n{bug_report}")
                development_plan['developer_task'] = str(bug_report)
            else:
                print(f"\n❌ Maximum retries ({max_retries}) reached. Proceeding to final report.")

        self._generate_final_report(technical_brief, test_results, development_plan)

    def _generate_final_report(self, brief, tests_output, dev_plan):
        """Compiles and prints the final report, and saves it as Markdown and HTML."""
        print("\n\n--- [Phase 3/3] Compiling Final Report ---")

        final_code = "Code could not be generated or finalized."
        final_tests = "Tests could not be generated or finalized."
        
        try:
            final_code = (WORKSPACE_DIR / dev_plan['file_name']).read_text()
        except Exception: pass

        try:
            final_tests = (WORKSPACE_DIR / dev_plan['test_file_name']).read_text()
        except Exception: pass
            
        final_outcome = "All tests passed successfully." if "ALL TESTS PASSED" in tests_output else "Process completed with failing tests."
        
        reporting_crew = Crew(agents=[self.agents['liaison']], tasks=[self.tasks['final_report']], verbose=False)
        final_report = reporting_crew.kickoff(
            inputs={
                'technical_brief': brief,
                'final_code': final_code,
                'final_tests': final_tests,
                'test_results': tests_output,
                'final_outcome_summary': final_outcome,
                'file_name': dev_plan.get('file_name', 'N/A'),
                'test_file_name': dev_plan.get('test_file_name', 'N/A')
            }
        )
        
        final_report_str = str(final_report)
        self._print_agent_output("Janus", "Client Liaison", "Compile the final client-facing report.", final_report_str)

        # Save the report
        report_file_stem = "Final_Report"
        # We need to extract just the markdown from the final report string
        match = re.search(r"```markdown(.*)```", final_report_str, re.S)
        markdown_content = match.group(1).strip() if match else final_report_str
        
        # Use the correct tool name 'save_report'
        save_result = save_report.func(file_name_stem=report_file_stem, markdown_content=markdown_content)
        print(f"\n📄 {save_result}")

        print("\n✅ Process Complete.")
        # FIX: Use os._exit for a more forceful exit to prevent hanging threads.
        os._exit(0)


if __name__ == "__main__":
    print("\n🚀 --- Initializing The Digital Forge --- 🚀")
    HARD_CODED_REQUEST = (
        "I need a Python function called `calculate_factorial` that takes a non-negative integer "
        "and returns its factorial. It should be in a file named `math_utils.py`. "
        "The function should handle the edge case of 0 (factorial of 0 is 1) and should raise a "
        "`ValueError` for negative numbers."
    )
    crew = DevelopmentCrew(HARD_CODED_REQUEST)
    crew.run()