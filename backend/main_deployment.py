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
        # === Phase 1: Initial Brief ===
        brief_result = create_technical_brief.run(inputs={"user_request": self.user_request})
        technical_brief = brief_result.output

        # === Phase 2: Plan ===
        plan_result = define_development_plan.run(inputs={"technical_brief": technical_brief})
        plan = plan_result.output  # This is a JSON string

        import json
        plan_data = json.loads(plan)
        file_name = plan_data["file_name"]
        test_file_name = plan_data["test_file_name"]
        developer_task = plan_data["developer_task"]
        tester_task = plan_data["tester_task"]

        # === Phase 3: Develop ===
        code_result = generate_python_code.run(inputs={
            "developer_task": developer_task,
            "file_name": file_name
        })
        saved_code_path = code_result.output

        test_result = generate_test_suite.run(inputs={
            "tester_task": tester_task,
            "file_name": file_name,
            "test_file_name": test_file_name
        })
        saved_test_path = test_result.output

        # === Phase 4: Test ===
        test_exec_result = execute_tests.run(inputs={
            "test_file_name": test_file_name
        })
        test_results = test_exec_result.output

        # === Phase 5: Debug (if tests failed) ===
        if test_results.strip() != "ALL TESTS PASSED":
            debug_result = analyze_test_failure.run(inputs={
                "developer_task": developer_task,
                "test_failure_log": test_results,
                "file_name": file_name,
                "test_file_name": test_file_name
            })

            debug_data = json.loads(debug_result.output)
            file_to_fix = debug_data["file_to_fix"]
            next_task = debug_data["next_task"]

            if file_to_fix == file_name:
                generate_python_code.run(inputs={
                    "developer_task": next_task,
                    "file_name": file_name
                })
            else:
                generate_test_suite.run(inputs={
                    "tester_task": next_task,
                    "file_name": file_name,
                    "test_file_name": test_file_name
                })

            # Run tests again
            test_exec_result = execute_tests.run(inputs={
                "test_file_name": test_file_name
            })
            test_results = test_exec_result.output

        # === Phase 6: Report ===
        # Read code and test content (in-memory fallback only)
        from tools.file_system_tools import read_file

        try:
            final_code = read_file(file_name)
        except Exception as e:
            final_code = f"Error: Code could not be read due to: {str(e)}"

        try:
            final_tests = read_file(test_file_name)
        except Exception as e:
            final_tests = f"Error: Test file could not be read due to: {str(e)}"

        report_result = compile_final_report.run(inputs={
            "technical_brief": technical_brief,
            "final_code": final_code,
            "final_tests": final_tests,
            "test_results": test_results,
            "file_name": file_name,
            "test_file_name": test_file_name,
            "final_outcome_summary": (
                "✅ All tests passed successfully."
                if test_results.strip() == "ALL TESTS PASSED"
                else "❌ Some tests failed. See the failure log below."
            )
        })

        return report_result.output