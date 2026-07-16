from pathlib import Path

from rag.evaluation.runner import (
    ApiEvaluationCase,
    GeneratedAnswer,
    RagEvaluationRunner,
    load_cases,
)
from rag.index import ChromaRetriever


class RequiredTermGenerator:
    def generate(
        self, case: ApiEvaluationCase, context: str, model: str
    ) -> GeneratedAnswer:
        assert model == "test-model"
        return GeneratedAnswer(text=" ".join(case.required_terms))


def test_api_evaluation_catalog_is_versioned_and_unique() -> None:
    cases = load_cases()

    assert len(cases) == 5
    assert len({case.id for case in cases}) == 5
    assert all(case.expected_source_ids for case in cases)


def test_rag_evaluation_records_configuration_sources_and_artifact(
    tmp_path: Path,
) -> None:
    report = RagEvaluationRunner(
        ChromaRetriever(),
        RequiredTermGenerator(),
        "test-model",
        tmp_path,
        use_retrieval=True,
    ).run()

    assert report.configuration == "rag"
    assert report.corpus_version == "1.0.0"
    assert report.cases_passed == report.cases_total == 5
    assert all(result.retrieval_passed for result in report.results)
    assert (tmp_path / report.run_id / "report.json").is_file()


def test_no_rag_evaluation_keeps_retrieval_score_separate(tmp_path: Path) -> None:
    report = RagEvaluationRunner(
        ChromaRetriever(),
        RequiredTermGenerator(),
        "test-model",
        tmp_path,
        use_retrieval=False,
    ).run(cases=load_cases()[:1])

    assert report.configuration == "no_rag"
    assert report.results[0].retrieval_passed is None
    assert report.results[0].retrieved_source_ids == ()
