"""The isolated Digital Forge orchestration pipeline."""

import json
import re
from collections.abc import Callable
from uuid import UUID

from crewai import Agent, Crew
from pydantic import BaseModel

from rag.index import get_retriever

from .agents import build_agents
from .artifact_validation import (
    normalize_test_imports,
    validate_application_artifact,
    validate_test_artifact,
)
from .config import Settings
from .models import (
    AttemptStatus,
    DevelopmentPlan,
    RunAgent,
    RunAttempt,
    RunEvent,
    RunResponse,
    RunStage,
    RunState,
    RunStatus,
)
from .retrieval import build_retrieval_tools
from .sandbox import build_sandbox_runner
from .self_healing import (
    FailureKind,
    failure_kind_from_output,
    infrastructure_retryable_from_output,
)
from .tasks import build_tasks
from .tools import build_file_system_tools

INFRASTRUCTURE_EXHAUSTED_MARKER = "INFRASTRUCTURE RETRIES EXHAUSTED"
INFRASTRUCTURE_CONFIGURATION_MARKER = "SANDBOX CONFIGURATION FAILURE"


def _parse_json(raw_output: object) -> dict[str, object]:
    structured_output = getattr(raw_output, "pydantic", None)
    if isinstance(structured_output, BaseModel):
        return structured_output.model_dump()

    json_output = getattr(raw_output, "json_dict", None)
    if isinstance(json_output, dict):
        return json_output

    cleaned = str(raw_output).strip().replace("```json", "").replace("```", "")
    parsed = json.loads(cleaned.strip())
    if not isinstance(parsed, dict):
        raise ValueError("Agent output must be a JSON object.")
    return parsed


class RunCancelled(Exception):
    """Raised at a workflow boundary after cancellation is requested."""


class DevelopmentCrew:
    def __init__(
        self,
        user_request: str,
        settings: Settings | None = None,
        *,
        run_id: UUID | None = None,
        on_update: Callable[[RunState], None] | None = None,
        is_cancel_requested: Callable[[], bool] | None = None,
    ):
        self.settings = settings or Settings()
        self.state = (
            RunState(run_id=run_id, request=user_request)
            if run_id is not None
            else RunState(request=user_request)
        )
        self.on_update = on_update
        self.is_cancel_requested = is_cancel_requested or (lambda: False)
        self.agents: dict[str, Agent] = build_agents(self.settings.openai_model_name)
        sandbox_runner = build_sandbox_runner(
            self.settings.sandbox_backend,
            self.settings.docker_sandbox_image,
            self.settings.modal_sandbox_app,
        )
        tools = build_file_system_tools(
            self.state.workspace,
            sandbox_runner,
            timeout_seconds=self.settings.sandbox_timeout_seconds,
            memory_mib=self.settings.sandbox_memory_mib,
            cpu_cores=self.settings.sandbox_cpu_cores,
            process_limit=self.settings.sandbox_process_limit,
        )
        retrieval_tools = build_retrieval_tools(
            get_retriever(self.settings.rag_index_path),
            self.state.retrieval_events,
            result_limit=self.settings.rag_result_limit,
        )
        self.run_tests_tool = next(tool for tool in tools if tool.name == "run_tests")
        self.tasks = build_tasks(self.agents, tools, retrieval_tools)

    def run(self) -> RunResponse:
        self.settings.require_openai_api_key()
        self.state.status = RunStatus.running
        try:
            self._transition(
                RunStage.briefing,
                "Janus is preparing the technical brief.",
                RunAgent.janus,
            )
            self._checkpoint()
            technical_brief = str(
                Crew(
                    agents=[self.agents["liaison"]],
                    tasks=[self.tasks.brief],
                    verbose=False,
                ).kickoff(inputs={"user_request": self.state.request})
            )
            self.state.technical_brief = technical_brief
            self._transition(
                RunStage.planning,
                "Athena is creating the development plan.",
                RunAgent.athena,
            )
            self._checkpoint()
            plan = DevelopmentPlan.model_validate(
                _parse_json(
                    Crew(
                        agents=[self.agents["lead"]],
                        tasks=[self.tasks.plan],
                        verbose=False,
                    ).kickoff(
                        inputs={
                            "user_request": self.state.request,
                            "technical_brief": technical_brief,
                        }
                    )
                )
            )
            self.state.plan = plan
            test_results = self._develop_and_test(plan)
            self.state.test_results = test_results
            self._transition(
                RunStage.reporting,
                "Janus is compiling the final report.",
                RunAgent.janus,
            )
            self._checkpoint()
            report = self._generate_final_report(technical_brief, test_results, plan)
            self.state.report = report
            self.state.status = (
                RunStatus.completed
                if "ALL TESTS PASSED" in test_results
                else RunStatus.failed
            )
            if self.state.status is RunStatus.completed:
                message = "The run completed and all tests passed."
            elif INFRASTRUCTURE_CONFIGURATION_MARKER in test_results:
                message = (
                    "The run stopped because the sandbox capability set is unavailable."
                )
            elif INFRASTRUCTURE_EXHAUSTED_MARKER in test_results:
                message = (
                    "The run stopped after repeated sandbox infrastructure failures."
                )
            else:
                message = "The run completed with failing tests."
            self._transition(RunStage.complete, message)
            return RunResponse(
                run_id=self.state.run_id,
                status=self.state.status,
                report=report,
                retrieval_events=tuple(self.state.retrieval_events),
            )
        except RunCancelled:
            self.state.status = RunStatus.cancelled
            self.state.report = "Run cancelled at the next safe workflow boundary."
            self._transition(RunStage.cancelled, "The run was cancelled.")
            return RunResponse(
                run_id=self.state.run_id,
                status=self.state.status,
                report=self.state.report,
                retrieval_events=tuple(self.state.retrieval_events),
            )
        except Exception:
            self.state.status = RunStatus.failed
            self._transition(
                RunStage.complete,
                "The pipeline stopped because an unexpected error occurred.",
            )
            raise

    def _develop_and_test(self, plan: DevelopmentPlan) -> str:
        developer_task = plan.developer_task
        tester_task = plan.tester_task
        test_results = ""
        candidate_attempts = 0
        infrastructure_retries = 0
        self._transition(
            RunStage.developing,
            "Hephaestus is writing application code.",
            RunAgent.hephaestus,
        )
        self._checkpoint()
        self._run_developer(plan, developer_task)
        self._transition(
            RunStage.developing,
            "Argus is writing the test suite.",
            RunAgent.argus,
        )
        self._checkpoint()
        self._run_test_author(plan, tester_task)

        while candidate_attempts < self.settings.max_attempts:
            self._transition(
                RunStage.testing,
                "Argus is running the generated tests.",
                RunAgent.argus,
            )
            self._checkpoint()
            test_results = self._run_tests(plan)
            failure_kind = failure_kind_from_output(test_results)
            if failure_kind is FailureKind.infrastructure:
                infrastructure_retries += 1
                self._record_attempt(
                    plan,
                    test_results,
                    failure_kind=failure_kind,
                    candidate_attempt=None,
                    repair_target="system",
                )
                if not infrastructure_retryable_from_output(test_results):
                    return (
                        f"{test_results}\n{INFRASTRUCTURE_CONFIGURATION_MARKER}: "
                        "candidate attempt was not consumed."
                    )
                if infrastructure_retries >= self.settings.max_attempts:
                    return (
                        f"{test_results}\n{INFRASTRUCTURE_EXHAUSTED_MARKER}: "
                        "candidate attempt was not consumed."
                    )
                continue

            infrastructure_retries = 0
            candidate_attempts += 1
            self.state.attempts = candidate_attempts
            if "ALL TESTS PASSED" in test_results:
                self._record_attempt(
                    plan,
                    test_results,
                    failure_kind=None,
                    candidate_attempt=candidate_attempts,
                    repair_target=None,
                )
                return test_results
            if candidate_attempts >= self.settings.max_attempts:
                self._record_attempt(
                    plan,
                    test_results,
                    failure_kind=failure_kind,
                    candidate_attempt=candidate_attempts,
                    repair_target=None,
                )
                return test_results

            if failure_kind is FailureKind.test:
                file_to_fix = plan.test_file_name
                next_task = (
                    "Repair only the current test suite using this sanitized failure "
                    "evidence. Re-audit every existing assertion against the original user "
                    "request before saving; fix unsupported expectations even when they are "
                    f"not named by this failure:\n{test_results}"
                )
            elif (
                failure_kind in {FailureKind.timeout, FailureKind.resource}
                or "REQUEST CONTRACT FAILURE:" in test_results
            ):
                file_to_fix = plan.file_name
                next_task = (
                    "Repair only the current application code using this sanitized "
                    f"failure evidence:\n{test_results}"
                )
            else:
                repair = self._analyze_failure(plan, test_results)
                file_to_fix = str(repair["file_to_fix"])
                next_task = str(repair["next_task"])
            repair_target = (
                "tests" if file_to_fix == plan.test_file_name else "application"
            )
            self._record_attempt(
                plan,
                test_results,
                failure_kind=failure_kind,
                candidate_attempt=candidate_attempts,
                repair_target=repair_target,
            )
            repair_subject = "test suite" if repair_target == "tests" else "application"
            self._transition(
                RunStage.repairing,
                f"The {repair_subject} is being repaired before the next attempt.",
                (RunAgent.argus if repair_target == "tests" else RunAgent.hephaestus),
            )
            self._checkpoint()
            if file_to_fix == plan.test_file_name:
                tester_task = next_task
                self._run_test_author(plan, tester_task)
            elif file_to_fix == plan.file_name:
                developer_task = next_task
                self._run_developer(plan, developer_task)
            else:
                raise ValueError("Repair target must be the application or test file.")
        return test_results

    def _record_attempt(
        self,
        plan: DevelopmentPlan,
        test_results: str,
        *,
        failure_kind: FailureKind | None,
        candidate_attempt: int | None,
        repair_target: str | None,
    ) -> None:
        status = AttemptStatus.passed
        if failure_kind is FailureKind.infrastructure:
            status = AttemptStatus.infrastructure
        elif "ALL TESTS PASSED" not in test_results:
            status = AttemptStatus.failed
        self.state.attempt_history.append(
            RunAttempt(
                sequence=len(self.state.attempt_history) + 1,
                candidate_attempt=candidate_attempt,
                status=status,
                failure_kind=failure_kind.value if failure_kind else None,
                repair_target=repair_target,
                test_results=test_results,
                application_code=self.state.workspace.read(plan.file_name) or "",
                test_code=self.state.workspace.read(plan.test_file_name) or "",
            )
        )
        self._notify()

    def _transition(
        self, stage: RunStage, message: str, agent: RunAgent | None = None
    ) -> None:
        self.state.stage = stage
        self.state.active_agent = agent
        self.state.events.append(RunEvent(stage=stage, message=message))
        self._notify()

    def _notify(self) -> None:
        if self.on_update is not None:
            self.on_update(self.state)

    def _checkpoint(self) -> None:
        if self.is_cancel_requested():
            raise RunCancelled

    def _run_developer(self, plan: DevelopmentPlan, developer_task: str) -> None:
        current_code = self.state.workspace.read(plan.file_name)
        Crew(
            agents=[self.agents["developer"]],
            tasks=[self.tasks.develop],
            verbose=False,
        ).kickoff(
            inputs={
                "original_developer_task": plan.developer_task,
                "user_request": self.state.request,
                "developer_task": developer_task,
                "file_name": plan.file_name,
                "current_code": current_code or "<no existing application code>",
            }
        )

    def _run_test_author(self, plan: DevelopmentPlan, tester_task: str) -> None:
        current_tests = self.state.workspace.read(plan.test_file_name)
        Crew(
            agents=[self.agents["tester"]],
            tasks=[self.tasks.test_suite],
            verbose=False,
        ).kickoff(
            inputs={
                "original_tester_task": plan.tester_task,
                "user_request": self.state.request,
                "tester_task": tester_task,
                "file_name": plan.file_name,
                "test_file_name": plan.test_file_name,
                "current_tests": current_tests or "<no existing test code>",
            }
        )

    def _run_tests(self, plan: DevelopmentPlan) -> str:
        application_code = self.state.workspace.read(plan.file_name)
        if application_code is not None:
            application_error = validate_application_artifact(
                self.state.request, application_code
            )
            if application_error:
                return (
                    "TESTS FAILED:\nFAILURE CLASS: candidate\n"
                    f"REQUEST CONTRACT FAILURE: {application_error}"
                )

        test_code = self.state.workspace.read(plan.test_file_name)
        if test_code is not None:
            normalized_test_code = normalize_test_imports(
                plan.file_name, self.state.request, test_code
            )
            if normalized_test_code != test_code:
                self.state.workspace.write(plan.test_file_name, normalized_test_code)
                test_code = normalized_test_code
            test_error = validate_test_artifact(
                plan.file_name, self.state.request, test_code
            )
            if test_error:
                return (
                    "TESTS FAILED:\nFAILURE CLASS: test\n"
                    f"TEST ARTIFACT FAILURE: {test_error}"
                )
        return str(self.run_tests_tool.run(test_file_path=plan.test_file_name))

    def _analyze_failure(
        self, plan: DevelopmentPlan, test_results: str
    ) -> dict[str, object]:
        current_code = self.state.workspace.read(plan.file_name)
        current_tests = self.state.workspace.read(plan.test_file_name)
        return _parse_json(
            Crew(
                agents=[self.agents["lead"]],
                tasks=[self.tasks.analyze_failure],
                verbose=False,
            ).kickoff(
                inputs={
                    "developer_task": plan.developer_task,
                    "user_request": self.state.request,
                    "test_failure_log": test_results,
                    "file_name": plan.file_name,
                    "test_file_name": plan.test_file_name,
                    "current_code": current_code or "<application code unavailable>",
                    "current_tests": current_tests or "<test code unavailable>",
                }
            )
        )

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
            else "Process stopped because the sandbox capability set is unavailable."
            if INFRASTRUCTURE_CONFIGURATION_MARKER in tests_output
            else "Process stopped after repeated sandbox infrastructure failures."
            if INFRASTRUCTURE_EXHAUSTED_MARKER in tests_output
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
                "retrieval_evidence": self._format_retrieval_evidence(),
            }
        )
        report = str(raw_report)
        match = re.search(r"```markdown(.*)```", report, re.DOTALL)
        return match.group(1).strip() if match else report

    def _format_retrieval_evidence(self) -> str:
        if not self.state.retrieval_events:
            return "No documentation sources were retrieved."
        lines = []
        for event in self.state.retrieval_events:
            for result in event.results:
                lines.append(
                    f"- {result.source_id}: {result.title} ({result.source_url}) "
                    f"for query: {event.query}"
                )
        return "\n".join(lines)
