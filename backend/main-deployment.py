# backend/main.py
# CLI entrypoint for Unit 734 - The Digital Forge (Production Ready)

import json
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process
import warnings
import os

# Suppress a known deprecation warning from a dependency (chromadb) to keep the output clean.
warnings.filterwarnings("ignore", category=DeprecationWarning)
# Disable crewAI's telemetry to prevent connection timeout errors.
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"

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

# Load environment variables
load_dotenv()

# Define workspace path for file reading
WORKSPACE_DIR = Path('backend/workspace')

class DevelopmentCrew:
    def __init__(self, user_request: str):
        self.user_request = user_request

    def _format_task_dictionary_to_string(self, task_dict: dict) -> str:
        """Helper function to format a task dictionary into a readable string."""
        formatted_string = ""
        for key, value in task_dict.items():
            title = key.replace('_', ' ').title()
            if isinstance(value, list):
                formatted_string += f"- {title}:\n"
                for item in value:
                    # Added another indent for nested items for better readability
                    formatted_string += f"    - {item}\n"
            else:
                formatted_string += f"- {title}: {value}\n"
        return formatted_string

    def run(self):
        """
        Runs the development crew process with production-ready logging, 
        ensuring a final report is always generated.
        """
        # These are now instance attributes, accessible throughout the class
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
        
        # Step 1: Create the Technical Brief
        brief_crew = Crew(agents=[self.agents['liaison']], tasks=[self.tasks['brief']], verbose=False)
        technical_brief = str(brief_crew.kickoff(inputs={'user_request': self.user_request}))
        print("Janus (Liaison): ✅ Technical Brief Created.")

        # Step 2: Create the Development Plan
        planning_crew = Crew(agents=[self.agents['lead']], tasks=[self.tasks['plan']], verbose=False)
        plan_output = planning_crew.kickoff(inputs={'technical_brief': technical_brief})
        
        try:
            clean_json_string = str(plan_output).strip().replace("```json", "").replace("```", "").strip()
            development_plan = json.loads(clean_json_string)
            print("Athena (Lead): ✅ Development Plan Created.")
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"❌ Error: Could not parse the development plan. Aborting. Error: {e}")
            self._generate_final_report(technical_brief, "Planning failed.", "No code generated.", "No tests generated.", {})
            return
        
        # Format tasks for clarity
        if isinstance(development_plan.get('developer_task'), dict):
            development_plan['developer_task'] = self._format_task_dictionary_to_string(development_plan['developer_task'])
        if isinstance(development_plan.get('tester_task'), dict):
            development_plan['tester_task'] = self._format_task_dictionary_to_string(development_plan['tester_task'])

        # --- [Phase 2/3] Development & Debugging ---
        print("\n--- [Phase 2/3] Development & Debugging ---")
        max_retries = 3
        test_results = ""
        
        for attempt in range(1, max_retries + 1):
            print(f"🚀 Sprint Attempt {attempt}/{max_retries}...")
            
            sprint_crew = Crew(
                agents=[self.agents['developer'], self.agents['tester']],
                tasks=[self.tasks['develop'], self.tasks['test_suite'], self.tasks['execute_tests']],
                process=Process.sequential,
                verbose=False,
                memory=True
            )
            
            test_results = str(sprint_crew.kickoff(inputs=development_plan.copy()))
            
            if "ALL TESTS PASSED" in test_results:
                print("Argus (Tester): ✅ All Tests Passed!")
                break
            
            print("Athena (Lead): ⚠️  Tests Failed. Analyzing and preparing for next attempt...")
            if attempt < max_retries:
                analysis_crew = Crew(
                    agents=[self.agents['lead']],
                    tasks=[self.tasks['analyze_failure']],
                    verbose=False
                )
                bug_report = analysis_crew.kickoff(inputs={
                    'test_failure_log': test_results,
                    'developer_task': development_plan['developer_task'],
                })
                development_plan['developer_task'] = str(bug_report)
            else:
                print(f"❌ Maximum retries ({max_retries}) reached. Proceeding to final report.")

        # --- [Phase 3/3] Final Report Generation ---
        self._generate_final_report(technical_brief, test_results, development_plan)

    def _generate_final_report(self, brief, tests_output, dev_plan):
        """Compiles and prints the final report."""
        print("\n--- [Phase 3/3] Compiling Final Report ---")

        final_code = "Code could not be generated or finalized."
        final_tests = "Tests could not be generated or finalized."
        
        try:
            final_code = (WORKSPACE_DIR / dev_plan['file_name']).read_text()
        except Exception:
            print(f"Warning: Could not read final code file.")

        try:
            final_tests = (WORKSPACE_DIR / dev_plan['test_file_name']).read_text()
        except Exception:
            print(f"Warning: Could not read final test file.")
            
        final_outcome = "All tests passed successfully." if "ALL TESTS PASSED" in tests_output else f"Process completed with failing tests."
        
        reporting_crew = Crew(
            agents=[self.agents['liaison']],
            tasks=[self.tasks['final_report']],
            verbose=False 
        )
        
        # FIX: Add the missing file_name and test_file_name to the inputs for the reporting crew
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
        
        print("\n\n====================================== FINAL REPORT ======================================")
        print(str(final_report))
        print("========================================================================================")
        print("✅ Process Complete.")


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