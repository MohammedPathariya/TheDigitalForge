# backend/main_deployment.py

import argparse, json, os, re, sys, traceback, logging, warnings
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process
from agents import unit_734_crew
from tasks import (
    create_technical_brief, define_development_plan,
    generate_python_code, generate_test_suite,
    execute_tests, analyze_test_failure,
    compile_final_report
)
from tools import read_file, save_report

# Load .env & suppress logs
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR.parent / '.env')
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not set."); sys.exit(1)
warnings.filterwarnings("ignore")
logging.getLogger('crewAI').setLevel(logging.CRITICAL)

WORKSPACE_DIR = ROOT_DIR / 'workspace'
WORKSPACE_DIR.mkdir(exist_ok=True)

class DevelopmentCrew:
    def __init__(self, user_request: str):
        self.user_request = user_request

    def run(self) -> str:
        try:
            # Phase 1: Brief
            brief = str(Crew([unit_734_crew['liaison']], [create_technical_brief], verbose=False)
                        .kickoff(inputs={'user_request': self.user_request}))

            # Phase 2: Plan
            plan_raw = str(Crew([unit_734_crew['lead']], [define_development_plan], verbose=False)
                           .kickoff(inputs={'technical_brief': brief}))
            plan_json = plan_raw.replace("```json","").replace("```","").strip()
            plan = json.loads(plan_json)
            fn, tfn = plan['file_name'], plan['test_file_name']
            dev_task, tst_task = plan['developer_task'], plan['tester_task']

            # Phase 3: Dev/Test loop
            result = ""
            for i in range(1, 4):
                Crew([unit_734_crew['developer']], [generate_python_code], verbose=False) \
                    .kickoff(inputs={'developer_task': dev_task, 'file_name': fn})

                result = str(Crew(
                    [unit_734_crew['tester']],
                    [generate_test_suite, execute_tests],
                    process=Process.sequential,
                    verbose=False
                ).kickoff(inputs={'tester_task': tst_task, 'file_name': fn, 'test_file_name': tfn}))

                if "ALL TESTS PASSED" in result:
                    break
                if i < 3:
                    bug_raw = str(Crew([unit_734_crew['lead']], [analyze_test_failure], verbose=False)
                                  .kickoff(inputs={
                                      'developer_task': dev_task,
                                      'test_failure_log': result,
                                      'file_name': fn,
                                      'test_file_name': tfn
                                  }))
                    bug_json = bug_raw.replace("```json","").replace("```","").strip()
                    bug = json.loads(bug_json)
                    if bug['file_to_fix'] == fn:
                        dev_task = bug['next_task']
                    else:
                        tst_task = bug['next_task']

            # Phase 4: Read code/tests
            final_code  = read_file.func(fn)
            final_tests = read_file.func(tfn)
            outcome = ("All tests passed successfully."
                       if "ALL TESTS PASSED" in result
                       else "Process completed with failing tests.")

            # Phase 5: Final report
            report_raw = str(Crew([unit_734_crew['liaison']], [compile_final_report], verbose=False)
                             .kickoff(inputs={
                                 'technical_brief': brief,
                                 'final_code': final_code,
                                 'final_tests': final_tests,
                                 'test_results': result,
                                 'file_name': fn,
                                 'test_file_name': tfn,
                                 'final_outcome_summary': outcome
                             }))
            m = re.search(r"```markdown(.*)```", report_raw, re.S)
            report = m.group(1).strip() if m else report_raw

            save_report.func("Final_Report", report)
            return report

        except Exception:
            traceback.print_exc()
            return "❌ A critical error occurred."

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("request"); a = p.parse_args()
    print(DevelopmentCrew(a.request).run())