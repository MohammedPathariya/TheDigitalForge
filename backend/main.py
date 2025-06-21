# backend/main.py
# CLI entrypoint for Unit 734 - The Digital Forge

from dotenv import load_dotenv
from crewai import Crew, Process

# --- Local Imports ---
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

# Load environment variables from .env file
load_dotenv()

class DevelopmentCrew:
    def __init__(self, user_request):
        self.user_request = user_request

    def run(self):
        # Initialize agents and tasks
        agents = unit_734_crew
        tasks = {
            'brief': create_technical_brief,
            'plan': define_development_plan,
            'develop': generate_python_code,
            'test_suite': generate_test_suite,
            'execute_tests': execute_tests,
            'analyze_failure': analyze_test_failure,
            'fix_code': fix_python_code,
            'final_report': compile_final_report
        }

        # Create the crew with a sequential process
        project_crew = Crew(
            agents=list(agents.values()),
            tasks=[
                tasks['brief'],
                tasks['plan'],
                tasks['develop'],
                tasks['test_suite'],
                tasks['execute_tests']
            ],
            process=Process.sequential,
            verbose=True
        )

        # Kick off the initial sprint
        print("\n--- Starting Initial Development Sprint ---")
        sprint_result = project_crew.kickoff(inputs={"user_request": self.user_request})

        # --- FIX: Convert the CrewOutput object to a string before checking its content ---
        sprint_output_str = str(sprint_result)

        # Check if tests failed and initiate the debugging loop if necessary
        if "FAILED" in sprint_output_str.upper():
            print("\n--- Tests Failed. Initiating Debugging Loop ---")
            
            # Re-define the crew for the debugging process
            debugging_crew = Crew(
                agents=[agents['lead'], agents['developer'], agents['tester']],
                tasks=[tasks['analyze_failure'], tasks['fix_code'], tasks['execute_tests']],
                process=Process.sequential,
                verbose=True
            )
            # The context from the first crew's failure is automatically passed
            debug_result = debugging_crew.kickoff()
            
            # --- FIX: Convert the debug result to a string as well ---
            debug_output_str = str(debug_result)

            if "ALL TESTS PASSED" in debug_output_str:
                print("\n--- Debugging Successful. Compiling Final Report ---")
                sprint_result = debug_result # Update result to the successful test run
            else:
                print("\n--- Debugging Failed. Could not fix the code. ---")
                return # End the process

        # If we reach here, all tests have passed.
        print("\n--- All Tests Passed. Compiling Final Report ---")
        
        # We need to explicitly pass the outputs of previous tasks as context
        # to the final reporting task. CrewAI doesn't automatically carry over
        # all context from one crew to another.
        tasks['final_report'].context = project_crew.tasks
        
        reporting_crew = Crew(
            agents=[agents['liaison']],
            tasks=[tasks['final_report']],
            verbose=True
        )
        final_report = reporting_crew.kickoff()

        print("\n\n--- Full Sprint Complete: Final Report ---")
        print("--------------------------------------------")
        print(final_report)
        print("--------------------------------------------")

if __name__ == "__main__":
    print("\n--- Starting 'The Digital Forge' CLI Runner ---")
    
    HARD_CODED_REQUEST = (
        "I need a Python function called `calculate_word_frequency` that takes a string of text. "
        "The function should return a dictionary where keys are the unique words and values are their counts. "
        "The analysis must be case-insensitive and all punctuation should be ignored. Numbers should NOT be counted as words."
    )
    
    digital_forge_crew = DevelopmentCrew(HARD_CODED_REQUEST)
    digital_forge_crew.run()