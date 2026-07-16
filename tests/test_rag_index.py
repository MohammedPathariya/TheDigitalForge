import json
from pathlib import Path

import pytest

from rag.index import (
    DEFAULT_MANIFEST_PATH,
    ChromaRetriever,
    build_index,
    load_manifest,
)


def test_bundled_index_retrieves_each_expected_api_source() -> None:
    retriever = ChromaRetriever()
    queries = {
        "OpenAI Responses store false output_text": "openai-responses-2-45-0",
        "FastAPI response_model filters output": "fastapi-models-0-139-0",
        "Pydantic Settings env nested delimiter": "pydantic-settings-2-10-1",
        "Modal Sandbox create exec wait": "modal-sandbox-1-5-1",
        "Chroma query_embeddings n_results": "chromadb-collections-1-1-1",
    }

    for query, expected_source_id in queries.items():
        source_ids = {result.source_id for result in retriever.retrieve(query, limit=3)}
        assert expected_source_id in source_ids


def test_bundled_index_contains_chroma_database() -> None:
    database_path = Path("rag/index/v1/chroma.sqlite3")

    assert database_path.is_file()
    assert database_path.stat().st_size > 0


def test_index_build_records_versioned_manifest_and_chunks(tmp_path: Path) -> None:
    metadata = build_index(DEFAULT_MANIFEST_PATH, tmp_path / "index")

    assert metadata.corpus_version == "1.0.0"
    assert metadata.chunk_count == 12
    assert (tmp_path / "index" / "chroma.sqlite3").is_file()


def test_manifest_rejects_modified_source_content(tmp_path: Path) -> None:
    source_root = DEFAULT_MANIFEST_PATH.parent
    copied_root = tmp_path / "sources"
    copied_content = copied_root / "content"
    copied_content.mkdir(parents=True)
    manifest_data = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
    for source in manifest_data["sources"]:
        source_path = source_root / source["content_path"]
        target = copied_root / source["content_path"]
        target.write_bytes(source_path.read_bytes())
    manifest_path = copied_root / "v1.json"
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
    first_source = copied_root / manifest_data["sources"][0]["content_path"]
    first_source.write_text("tampered", encoding="utf-8")

    with pytest.raises(ValueError, match="digest mismatch"):
        load_manifest(manifest_path)


def test_retriever_rejects_manifest_that_does_not_match_index(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="manifest does not match"):
        ChromaRetriever(manifest_path=manifest_path)
