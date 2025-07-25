# backend/main_deployment.py

from crewai import Crew
from agents import unit_734_crew
from tasks import (
    create_technical_brief,
    decompose_plan,
    write_code,
    test_code,
    analyze_bug,
    fix_code,
    retest_code,
    generate_report
)

class DevelopmentCrew:
    def __init__(self, user_request: str):
        self.crew = Crew(
            agents=unit_734_crew,
            tasks=[
                create_technical_brief,
                decompose_plan,
                write_code,
                test_code,
                analyze_bug,
                fix_code,
                retest_code,
                generate_report
            ],
            verbose=True,
            step_callback=self.log_step
        )
        self.user_request = user_request
        self.full_output = ""

    def log_step(self, step_output: str):
        print(step_output)
        self.full_output += step_output + "\n"

    def run_pipeline(self) -> str:
        result = self.crew.run({"user_request": self.user_request})
        self.full_output += f"\n---FINAL_REPORT---\n{result}"
        return self.full_output