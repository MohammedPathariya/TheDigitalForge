# backend/main.py
# CLI entrypoint for Unit 734 - The Digital Forge

import json
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process

from agents import unit_734_crew
from tasks import (
    create_technical_brief,
    define_development_plan,
    generate_python_code,
    generate_test_suite,
    execute_tests,
    analyze_test_failure,
    fix_python_code,
    compile_final_report
)
from tools import file_system_tools

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
            # Format keys to be more readable
            title = key.replace('_', ' ').title()
            if isinstance(value, list):
                # Format lists with bullet points
                formatted_string += f"- {title}:\n"
                for item in value:
                    formatted_string += f"  - {item}\n"
            else:
                formatted_string += f"- {title}: {value}\n"
        return formatted_string

    def run(self):
        agents = unit_734_crew
        tasks = {
            'brief': create_technical_brief,
            'plan': define_development_plan,
            'develop': generate_python_code,
            'test_suite': generate_test_suite,
            'execute_tests': execute_tests,
            'analyze_failure': analyze_test_failure,
            'fix_code': fix_python_code,
            'final_report': compile_final_report,
        }

        # --- Step 1: Create the Technical Brief ---
        print("\n--- Step 1: Janus is creating the Technical Brief ---")
        brief_crew = Crew(
            agents=[agents['liaison']],
            tasks=[tasks['brief']],
            verbose=True
        )
        brief_output = brief_crew.kickoff(inputs={'user_request': self.user_request})
        
        technical_brief = str(brief_output)
        print("\n--- Technical Brief Created ---\n", technical_brief)


        # --- Step 2: Create the Development Plan ---
        print("\n--- Step 2: Athena is creating the Development Plan ---")
        planning_crew = Crew(
            agents=[agents['lead']],
            tasks=[tasks['plan']],
            verbose=True
        )
        plan_output = planning_crew.kickoff(inputs={'technical_brief': technical_brief})

        try:
            # Clean the string: remove markdown code fences and whitespace
            clean_json_string = str(plan_output).strip().replace("```json", "").replace("```", "").strip()
            development_plan = json.loads(clean_json_string)
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Warning: Could not parse the development plan. Error: {e}. Aborting.")
            return
            
        print("\n--- Development Plan Created ---\n", json.dumps(development_plan, indent=2))

        # --- FIX: Convert complex task objects to simple, readable strings ---
        # This prevents ambiguity and ensures the developer/tester agents get clear instructions.
        if isinstance(development_plan.get('developer_task'), dict):
            development_plan['developer_task'] = self._format_task_dictionary_to_string(development_plan['developer_task'])
        
        if isinstance(development_plan.get('tester_task'), dict):
            development_plan['tester_task'] = self._format_task_dictionary_to_string(development_plan['tester_task'])

        # --- Development & Debugging Loop ---
        max_retries = 3 # Increased retries to allow for more complex debugging.
        for attempt in range(1, max_retries + 1):
            print(f"\n--- Development Sprint: Attempt {attempt}/{max_retries} ---")
            
            # The sprint crew now receives string-based tasks
            sprint_crew = Crew(
                agents=[agents['developer'], agents['tester']],
                tasks=[tasks['develop'], tasks['test_suite'], tasks['execute_tests']],
                process=Process.sequential,
                verbose=True,
                memory=True
            )
            
            test_results = sprint_crew.kickoff(inputs=development_plan.copy())
            print("\n--- Test Results ---\n", test_results)

            if "ALL TESTS PASSED" in str(test_results):
                print("\n--- All Tests Passed! Generating Final Report ---")

                try:
                    final_code = (WORKSPACE_DIR / development_plan['file_name']).read_text()
                    final_tests = (WORKSPACE_DIR / development_plan['test_file_name']).read_text()
                except FileNotFoundError:
                    print(f"Error: Could not find {development_plan['file_name']} or {development_plan['test_file_name']} to generate report.")
                    return

                reporting_crew = Crew(
                    agents=[agents['liaison']],
                    tasks=[tasks['final_report']],
                    verbose=True
                )
                
                final_report = reporting_crew.kickoff(
                    inputs={
                        'technical_brief': technical_brief,
                        'final_code': final_code,
                        'final_tests': final_tests,
                        'file_name': development_plan['file_name'],
                        'test_file_name': development_plan['test_file_name']
                    }
                )
                print("\n--- Final Report ---\n", str(final_report))
                return

            if attempt < max_retries:
                print("\n--- Tests Failed. Running Debugging Step ---")
                analysis_crew = Crew(
                    agents=[agents['lead']],
                    tasks=[tasks['analyze_failure']],
                    verbose=True
                )
                bug_report = analysis_crew.kickoff(inputs={
                    'test_failure_log': str(test_results),
                    'developer_task': development_plan['developer_task'],
                })
                print("\n--- Bug Report from Athena ---\n", bug_report)
                # Update the developer task with the new instructions for the next loop.
                development_plan['developer_task'] = str(bug_report)
            else:
                print(f"\n--- Maximum retries ({max_retries}) reached. Exiting. ---")
                return

if __name__ == "__main__":
    print("\n--- Starting 'The Digital Forge' CLI Runner ---")
    HARD_CODED_REQUEST = (
         "I need a Python function called `calculate_factorial` that takes a non-negative integer "
        "and returns its factorial. It should be in a file named `math_utils.py`. "
        "The function should handle the edge case of 0 (factorial of 0 is 1) and should raise a "
        "`ValueError` for negative numbers."
    )
    crew = DevelopmentCrew(HARD_CODED_REQUEST)
    crew.run()