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
        
        # --- THIS IS THE FIX ---
        # Convert CrewOutput to a string before using it as input for the next task.
        technical_brief = str(brief_output)
        # ----------------------

        print("\n--- Technical Brief Created ---\n", technical_brief)


        # --- Step 2: Create the Development Plan ---
        print("\n--- Step 2: Athena is creating the Development Plan ---")
        planning_crew = Crew(
            agents=[agents['lead']],
            tasks=[tasks['plan']],
            verbose=True
        )
        # Now, pass the clean string variable as context
        plan_output = planning_crew.kickoff(inputs={'technical_brief': technical_brief})

        # The output from a single-agent crew is the raw string, ready for parsing
        try:
            # Clean the string: remove ```python ... ``` and other markdown
            clean_json_string = str(plan_output).strip().removeprefix("```python").removesuffix("```").strip()
            development_plan = json.loads(clean_json_string)
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Warning: Could not parse the development plan. Error: {e}. Using raw output.")
            # Fallback if parsing fails
            development_plan = {
                'developer_task': str(plan_output),
                'tester_task': "Create a comprehensive pytest suite to validate the code based on the technical brief."
            }
        print("\n--- Development Plan Created ---\n", json.dumps(development_plan, indent=2))

        # --- Development & Debugging Loop ---
        max_retries = 2
        for attempt in range(1, max_retries + 1):
            print(f"\n--- Development Sprint: Attempt {attempt}/{max_retries} ---")
            
            sprint_tasks = [
                tasks['develop'],
                tasks['test_suite'],
                tasks['execute_tests']
            ]

            sprint_crew = Crew(
                agents=[agents['developer'], agents['tester']],
                tasks=sprint_tasks,
                process=Process.sequential,
                verbose=True,
                memory=True
            )
            test_results = sprint_crew.kickoff(inputs=development_plan)
            print("\n--- Test Results ---\n", test_results)

            if "ALL TESTS PASSED" in str(test_results):
                print("\n--- All Tests Passed! Generating Final Report ---")

                try:
                    final_code = (WORKSPACE_DIR / 'product.py').read_text()
                    final_tests = (WORKSPACE_DIR / 'test_product.py').read_text()
                except FileNotFoundError:
                    print("Error: Could not find product.py or test_product.py to generate report.")
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
                        'final_tests': final_tests
                    }
                )
                print("\n--- Final Report ---\n", str(final_report)) # Also convert final report to string
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
                development_plan['developer_task'] = str(bug_report)
            else:
                print("\n--- Maximum retries reached. Exiting. ---")
                return

if __name__ == "__main__":
    print("\n--- Starting 'The Digital Forge' CLI Runner ---")
    HARD_CODED_REQUEST = (
        "I need a Python function called `analyze_text` that takes a string. "
        "It should return a dictionary of word frequencies. "
        "The analysis must be case-insensitive. All punctuation should be ignored, "
        "**except for apostrophes within words** (e.g., it's, user's). "
        "Standalone numbers should be ignored."
    )
    crew = DevelopmentCrew(HARD_CODED_REQUEST)
    crew.run()