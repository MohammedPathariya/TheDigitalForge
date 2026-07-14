"""The isolated Digital Forge orchestration pipeline."""

import json
import re

from crewai import Agent, Crew, Process

from .agents import build_agents
from .config import Settings
from .models import DevelopmentPlan, RunResponse, RunState, RunStatus
from .tasks import build_tasks
from .tools import build_file_system_tools


def _parse_json(raw_output: object) -> dict[str, object]:
    cleaned = str(raw_output).strip().replace("```json", "").replace("```", "")
    parsed = json.loads(cleaned.strip())
    if not isinstance(parsed, dict):
        raise ValueError("Agent output must be a JSON object.")
    return parsed


class DevelopmentCrew:
    def __init__(self, user_request: str, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.state = RunState(request=user_request)
        self.agents: dict[str, Agent] = build_agents()
        tools = build_file_system_tools(self.state.workspace)
        self.tasks = build_tasks(self.agents, tools)

    def run(self) -> RunResponse:
        self.settings.require_openai_api_key()
        self.state.status = RunStatus.running
        try:
            technical_brief = str(
                Crew(
                    agents=[self.agents["liaison"]],
                    tasks=[self.tasks.brief],
                    verbose=False,
                ).kickoff(inputs={"user_request": self.state.request})
            )
            self.state.technical_brief = technical_brief
            plan = DevelopmentPlan.model_validate(
                _parse_json(
                    Crew(
                        agents=[self.agents["lead"]],
                        tasks=[self.tasks.plan],
                        verbose=False,
                    ).kickoff(inputs={"technical_brief": technical_brief})
                )
            )
            self.state.plan = plan
            test_results = self._develop_and_test(plan)
            self.state.test_results = test_results
            report = self._generate_final_report(technical_brief, test_results, plan)
            self.state.report = report
            self.state.status = (
                RunStatus.completed
                if "ALL TESTS PASSED" in test_results
                else RunStatus.failed
            )
            return RunResponse(
                run_id=self.state.run_id,
                status=self.state.status,
                report=report,
            )
        except Exception:
            self.state.status = RunStatus.failed
            raise

    def _develop_and_test(self, plan: DevelopmentPlan) -> str:
        developer_task = plan.developer_task
        tester_task = plan.tester_task
        test_results = ""
        for attempt in range(1, self.settings.max_attempts + 1):
            self.state.attempts = attempt
            Crew(
                agents=[self.agents["developer"]],
                tasks=[self.tasks.develop],
                verbose=False,
            ).kickoff(
                inputs={
                    "developer_task": developer_task,
                    "file_name": plan.file_name,
                }
            )
            test_results = str(
                Crew(
                    agents=[self.agents["tester"]],
                    tasks=[self.tasks.test_suite, self.tasks.execute_tests],
                    process=Process.sequential,
                    verbose=False,
                ).kickoff(
                    inputs={
                        "tester_task": tester_task,
                        "file_name": plan.file_name,
                        "test_file_name": plan.test_file_name,
                    }
                )
            )
            if "ALL TESTS PASSED" in test_results:
                break
            if attempt < self.settings.max_attempts:
                repair = _parse_json(
                    Crew(
                        agents=[self.agents["lead"]],
                        tasks=[self.tasks.analyze_failure],
                        verbose=False,
                    ).kickoff(
                        inputs={
                            "developer_task": plan.developer_task,
                            "test_failure_log": test_results,
                            "file_name": plan.file_name,
                            "test_file_name": plan.test_file_name,
                        }
                    )
                )
                next_task = str(repair["next_task"])
                if repair.get("file_to_fix") == plan.test_file_name:
                    tester_task = next_task
                else:
                    developer_task = next_task
        return test_results

    def _generate_final_report(
        self, brief: str, tests_output: str, plan: DevelopmentPlan
    ) -> str:
        final_code = self.state.workspace.read(plan.file_name)
        final_tests = self.state.workspace.read(plan.test_file_name)
        if final_code is None:
            final_code = f"Error: Code for {plan.file_name} not found in memory."
        if final_tests is None:
            final_tests = f"Error: Tests for {plan.test_file_name} not found in memory."
        outcome = (
            "All tests passed successfully."
            if "ALL TESTS PASSED" in tests_output
            else "Process completed with failing tests."
        )
        raw_report = Crew(
            agents=[self.agents["liaison"]],
            tasks=[self.tasks.final_report],
            verbose=False,
        ).kickoff(
            inputs={
                "technical_brief": brief,
                "final_code": final_code,
                "final_tests": final_tests,
                "test_results": tests_output,
                "file_name": plan.file_name,
                "test_file_name": plan.test_file_name,
                "final_outcome_summary": outcome,
            }
        )
        report = str(raw_report)
        match = re.search(r"```markdown(.*)```", report, re.DOTALL)
        return match.group(1).strip() if match else report
