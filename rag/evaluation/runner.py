"""Run separate RAG and no-RAG API documentation evaluations."""

import argparse
import json
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from rag.index import DEFAULT_INDEX_PATH, ChromaRetriever
from rag.models import RetrievedSource

DEFAULT_CASES_PATH = Path(__file__).with_name("cases") / "v1.json"
EVALUATION_VERSION = "1.0.0"
PROMPT_VERSION = "api-grounding-v1"


class ApiEvaluationCase(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^rag_api_\d{2}$")
    prompt: str
    expected_source_ids: tuple[str, ...]
    required_terms: tuple[str, ...]
    forbidden_terms: tuple[str, ...] = ()


class GeneratedAnswer(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    response_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ApiEvaluationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str
    passed: bool
    retrieval_passed: bool | None
    retrieved_source_ids: tuple[str, ...]
    answer: str
    missing_terms: tuple[str, ...]
    forbidden_terms_found: tuple[str, ...]
    response_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None


class ApiEvaluationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    evaluation_version: str = EVALUATION_VERSION
    corpus_version: str
    prompt_version: str = PROMPT_VERSION
    configuration: str
    run_id: str
    model: str
    started_at: datetime
    completed_at: datetime
    cases_passed: int = Field(ge=0)
    cases_total: int = Field(ge=0)
    results: tuple[ApiEvaluationResult, ...]


class AnswerGenerator(Protocol):
    def generate(
        self, case: ApiEvaluationCase, context: str, model: str
    ) -> GeneratedAnswer: ...


class OpenAIAnswerGenerator:
    def __init__(self, client: OpenAI | None = None):
        self.client = client or OpenAI()

    def generate(
        self, case: ApiEvaluationCase, context: str, model: str
    ) -> GeneratedAnswer:
        instructions = (
            "Answer the API question concisely. Use exact Python API names. Do not invent "
            "methods or parameters. When documentation context is supplied, use only that "
            "context for library-specific claims."
        )
        input_text = case.prompt
        if context:
            input_text = f"{case.prompt}\n\nPINNED DOCUMENTATION:\n{context}"
        response = self.client.responses.create(
            model=model,
            instructions=instructions,
            input=input_text,
            store=False,
        )
        usage = response.usage
        return GeneratedAnswer(
            text=response.output_text,
            response_id=response.id,
            input_tokens=usage.input_tokens if usage else None,
            output_tokens=usage.output_tokens if usage else None,
        )


class RagEvaluationRunner:
    def __init__(
        self,
        retriever: ChromaRetriever,
        generator: AnswerGenerator,
        model: str,
        output_root: Path,
        *,
        use_retrieval: bool,
    ):
        self.retriever = retriever
        self.generator = generator
        self.model = model
        self.output_root = output_root
        self.use_retrieval = use_retrieval

    def run(
        self, cases: Sequence[ApiEvaluationCase] | None = None
    ) -> ApiEvaluationReport:
        selected = tuple(cases) if cases is not None else load_cases()
        run_id = uuid4().hex
        started_at = datetime.now(timezone.utc)
        results = tuple(self._run_case(case) for case in selected)
        report = ApiEvaluationReport(
            corpus_version=self.retriever.metadata.corpus_version,
            configuration="rag" if self.use_retrieval else "no_rag",
            run_id=run_id,
            model=self.model,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            cases_passed=sum(result.passed for result in results),
            cases_total=len(results),
            results=results,
        )
        run_directory = self.output_root / run_id
        run_directory.mkdir(parents=True, exist_ok=False)
        (run_directory / "report.json").write_text(
            report.model_dump_json(indent=2), encoding="utf-8"
        )
        return report

    def _run_case(self, case: ApiEvaluationCase) -> ApiEvaluationResult:
        sources: tuple[RetrievedSource, ...] = ()
        try:
            if self.use_retrieval:
                sources = self.retriever.retrieve(case.prompt, limit=3)
            context = format_context(sources)
            generated = self.generator.generate(case, context, self.model)
            normalized = generated.text.lower()
            missing = tuple(
                term for term in case.required_terms if term.lower() not in normalized
            )
            forbidden = tuple(
                term for term in case.forbidden_terms if term.lower() in normalized
            )
            source_ids = tuple(dict.fromkeys(source.source_id for source in sources))
            retrieval_passed = (
                all(source_id in source_ids for source_id in case.expected_source_ids)
                if self.use_retrieval
                else None
            )
            passed = not missing and not forbidden and retrieval_passed is not False
            return ApiEvaluationResult(
                case_id=case.id,
                passed=passed,
                retrieval_passed=retrieval_passed,
                retrieved_source_ids=source_ids,
                answer=generated.text,
                missing_terms=missing,
                forbidden_terms_found=forbidden,
                response_id=generated.response_id,
                input_tokens=generated.input_tokens,
                output_tokens=generated.output_tokens,
            )
        except Exception as exc:
            return ApiEvaluationResult(
                case_id=case.id,
                passed=False,
                retrieval_passed=False if self.use_retrieval else None,
                retrieved_source_ids=tuple(
                    dict.fromkeys(source.source_id for source in sources)
                ),
                answer="",
                missing_terms=case.required_terms,
                forbidden_terms_found=(),
                error=f"{type(exc).__name__}: {exc}",
            )


def load_cases(path: Path = DEFAULT_CASES_PATH) -> tuple[ApiEvaluationCase, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases = TypeAdapter(tuple[ApiEvaluationCase, ...]).validate_python(raw)
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("RAG evaluation case IDs must be unique.")
    return cases


def format_context(sources: Sequence[RetrievedSource]) -> str:
    return "\n\n".join(
        f"[{source.source_id}] {source.title} / {source.heading}\n"
        f"{source.content}\nSource: {source.source_url}"
        for source in sources
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the API-focused RAG evaluation")
    parser.add_argument(
        "--model", required=True, help="Exact OpenAI model ID to record"
    )
    parser.add_argument("--configuration", choices=("rag", "no-rag"), required=True)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--output", type=Path, default=Path("rag-evaluation-results"))
    args = parser.parse_args(argv)
    report = RagEvaluationRunner(
        ChromaRetriever(args.index),
        OpenAIAnswerGenerator(),
        args.model,
        args.output,
        use_retrieval=args.configuration == "rag",
    ).run()
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
