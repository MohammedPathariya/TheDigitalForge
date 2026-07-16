"""Build and query the bundled ChromaDB documentation index."""

import argparse
import hashlib
import math
import re
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import chromadb
from chromadb.api import ClientAPI
from chromadb.config import Settings as ChromaSettings

from .models import (
    DocumentationChunk,
    IndexMetadata,
    RetrievedSource,
    SourceManifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "rag" / "sources" / "v1.json"
DEFAULT_INDEX_PATH = PROJECT_ROOT / "rag" / "index" / "v1"
COLLECTION_NAME = "digital_forge_docs_v1"
EMBEDDING_DIMENSIONS = 256
EMBEDDING_VERSION = f"token-hash-v1-{EMBEDDING_DIMENSIONS}"
INDEX_METADATA_FILE = "index.json"
_TOKEN = re.compile(r"[a-z0-9_\.]+")


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> SourceManifest:
    manifest = SourceManifest.model_validate_json(path.read_text(encoding="utf-8"))
    ids = [source.id for source in manifest.sources]
    if len(ids) != len(set(ids)):
        raise ValueError("Documentation source IDs must be unique.")
    for source in manifest.sources:
        content_path = path.parent / source.content_path
        digest = hashlib.sha256(content_path.read_bytes()).hexdigest()
        if digest != source.sha256:
            raise ValueError(f"Documentation source digest mismatch: {source.id}")
    return manifest


def load_chunks(
    manifest: SourceManifest, manifest_path: Path = DEFAULT_MANIFEST_PATH
) -> tuple[DocumentationChunk, ...]:
    chunks: list[DocumentationChunk] = []
    for source in manifest.sources:
        content = (manifest_path.parent / source.content_path).read_text(
            encoding="utf-8"
        )
        sections = _split_sections(content)
        for index, (heading, section) in enumerate(sections):
            chunks.append(
                DocumentationChunk(
                    id=f"{source.id}:{index:02d}",
                    source=source,
                    heading=heading,
                    content=section,
                    chunk_index=index,
                )
            )
    if not chunks:
        raise ValueError("Documentation corpus produced no chunks.")
    return tuple(chunks)


def embed_text(value: str) -> list[float]:
    tokens = _TOKEN.findall(value.lower())
    features = tokens + [f"{left}::{right}" for left, right in zip(tokens, tokens[1:])]
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for feature in features:
        digest = hashlib.blake2b(feature.encode(), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(component * component for component in vector))
    if norm == 0:
        return vector
    return [component / norm for component in vector]


def build_index(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    index_path: Path = DEFAULT_INDEX_PATH,
) -> IndexMetadata:
    manifest = load_manifest(manifest_path)
    chunks = load_chunks(manifest, manifest_path)
    index_path.mkdir(parents=True, exist_ok=True)
    client = _client(index_path)
    if COLLECTION_NAME in {collection.name for collection in client.list_collections()}:
        client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
        metadata={
            "corpus_version": manifest.corpus_version,
            "embedding_version": EMBEDDING_VERSION,
        },
    )
    embeddings: list[Sequence[float]] = [
        embed_text(
            f"{chunk.source.library} {chunk.source.title} {chunk.heading} "
            f"{chunk.content}"
        )
        for chunk in chunks
    ]
    collection.upsert(
        ids=[chunk.id for chunk in chunks],
        embeddings=embeddings,
        documents=[chunk.content for chunk in chunks],
        metadatas=[
            {
                "source_id": chunk.source.id,
                "library": chunk.source.library,
                "library_version": chunk.source.library_version,
                "document_version": chunk.source.document_version,
                "title": chunk.source.title,
                "heading": chunk.heading,
                "source_url": chunk.source.source_url,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ],
    )
    metadata = IndexMetadata(
        corpus_version=manifest.corpus_version,
        collection_name=COLLECTION_NAME,
        embedding_version=EMBEDDING_VERSION,
        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        chunk_count=len(chunks),
    )
    (index_path / INDEX_METADATA_FILE).write_text(
        metadata.model_dump_json(indent=2), encoding="utf-8"
    )
    return metadata


class ChromaRetriever:
    def __init__(
        self,
        index_path: Path = DEFAULT_INDEX_PATH,
        manifest_path: Path = DEFAULT_MANIFEST_PATH,
    ):
        metadata_path = index_path / INDEX_METADATA_FILE
        if not metadata_path.is_file():
            raise FileNotFoundError(f"RAG index metadata not found: {metadata_path}")
        self.metadata = IndexMetadata.model_validate_json(
            metadata_path.read_text(encoding="utf-8")
        )
        manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        if manifest_digest != self.metadata.manifest_sha256:
            raise ValueError("RAG index manifest does not match its metadata.")
        manifest = load_manifest(manifest_path)
        if manifest.corpus_version != self.metadata.corpus_version:
            raise ValueError("RAG index corpus version does not match its manifest.")
        if self.metadata.embedding_version != EMBEDDING_VERSION:
            raise ValueError("RAG index embedding version is incompatible.")
        self._collection = _client(index_path).get_collection(
            self.metadata.collection_name, embedding_function=None
        )
        if self._collection.count() != self.metadata.chunk_count:
            raise ValueError("RAG index chunk count does not match its metadata.")

    def retrieve(self, query: str, limit: int = 3) -> tuple[RetrievedSource, ...]:
        normalized = query.strip()
        if not normalized:
            raise ValueError("Documentation query cannot be empty.")
        if not 1 <= limit <= 5:
            raise ValueError("Documentation result limit must be between 1 and 5.")
        candidate_count = min(self.metadata.chunk_count, max(limit * 4, limit))
        query_embedding: Sequence[float] = embed_text(normalized)
        raw = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=candidate_count,
            include=["documents", "metadatas", "distances"],
        )
        ids = raw["ids"][0]
        documents = cast(list[list[str]], raw["documents"])[0]
        metadatas = cast(list[list[dict[str, Any]]], raw["metadatas"])[0]
        distances = cast(list[list[float]], raw["distances"])[0]
        candidates = tuple(zip(ids, documents, metadatas, distances, strict=True))
        query_tokens = set(_TOKEN.findall(normalized.lower()))
        mentioned_libraries = {
            str(metadata["library"])
            for _, _, metadata, _ in candidates
            if _library_is_mentioned(query_tokens, str(metadata["library"]))
        }
        relevant = tuple(
            item
            for item in candidates
            if (
                str(item[2]["library"]) in mentioned_libraries
                if mentioned_libraries
                else _lexical_score(normalized, f"{item[2]} {item[1]}") > 0
            )
        )
        ranked = sorted(
            relevant,
            key=lambda item: (
                -_lexical_score(normalized, f"{item[2]} {item[1]}"),
                item[3],
                item[0],
            ),
        )
        return tuple(_retrieved_source(*item) for item in ranked[:limit])


@lru_cache(maxsize=8)
def get_retriever(
    index_path: Path = DEFAULT_INDEX_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> ChromaRetriever:
    return ChromaRetriever(index_path, manifest_path)


def _client(index_path: Path) -> ClientAPI:
    return chromadb.PersistentClient(
        path=index_path,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _split_sections(content: str) -> tuple[tuple[str, str], ...]:
    heading = "Overview"
    body: list[str] = []
    sections: list[tuple[str, str]] = []
    for line in content.splitlines():
        if line.startswith("## "):
            if body:
                sections.append((heading, "\n".join(body).strip()))
            heading = line.removeprefix("## ").strip()
            body = []
        elif not line.startswith("# "):
            body.append(line)
    if body:
        sections.append((heading, "\n".join(body).strip()))
    return tuple((title, section) for title, section in sections if section)


def _lexical_score(query: str, value: str) -> int:
    query_tokens = set(_TOKEN.findall(query.lower()))
    value_tokens = set(_TOKEN.findall(value.lower()))
    return len(query_tokens & value_tokens)


def _library_is_mentioned(query_tokens: set[str], library: str) -> bool:
    library_tokens = set(_TOKEN.findall(library.lower().replace("-", " ")))
    return bool(library_tokens) and library_tokens <= query_tokens


def _retrieved_source(
    chunk_id: str,
    content: str,
    metadata: dict[str, Any],
    distance: float,
) -> RetrievedSource:
    return RetrievedSource(
        chunk_id=chunk_id,
        source_id=str(metadata["source_id"]),
        library=str(metadata["library"]),
        library_version=str(metadata["library_version"]),
        document_version=str(metadata["document_version"]),
        title=str(metadata["title"]),
        heading=str(metadata["heading"]),
        source_url=str(metadata["source_url"]),
        content=content,
        distance=max(0.0, distance),
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build the versioned ChromaDB index")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_INDEX_PATH)
    args = parser.parse_args(argv)
    print(build_index(args.manifest, args.output).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
