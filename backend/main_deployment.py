# backend/main_deployment.py

from crewai import Crew
from tasks import (
    create_technical_brief,
    define_development_plan,
    generate_python_code,
    generate_test_suite,
    execute_tests,
    analyze_test_failure,
    compile_final_report
)

class DevelopmentCrew:
    def __init__(self, user_request):
        self.user_request = user_request

    def run_pipeline(self):
        print("🧠 Starting Crew for:", self.user_request)

        crew = Crew(
            agents=[
                create_technical_brief.agent,
                define_development_plan.agent,
                generate_python_code.agent,
                generate_test_suite.agent,
                execute_tests.agent,
                analyze_test_failure.agent,
                compile_final_report.agent
            ],
            tasks=[
                create_technical_brief,
                define_development_plan,
                generate_python_code,
                generate_test_suite,
                execute_tests,
                analyze_test_failure,
                compile_final_report
            ],
            verbose=True
        )

        result = crew.kickoff(
            inputs={"user_request": self.user_request}
        )

        return result