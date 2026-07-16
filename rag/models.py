"""Typed models for documentation sources, retrieval, and index metadata."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class DocumentationSource(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]+$")
    library: str
    library_version: str
    document_version: str
    title: str
    source_url: str = Field(pattern=r"^https://")
    content_path: Path
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class SourceManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    corpus_version: str
    sources: tuple[DocumentationSource, ...]


class DocumentationChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    source: DocumentationSource
    heading: str
    content: str
    chunk_index: int = Field(ge=0)


class RetrievedSource(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: str
    source_id: str
    library: str
    library_version: str
    document_version: str
    title: str
    heading: str
    source_url: str
    content: str = Field(exclude=True)
    distance: float = Field(ge=0)


class RetrievalEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    query: str
    results: tuple[RetrievedSource, ...]


class IndexMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    corpus_version: str
    collection_name: str
    embedding_version: str
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    chunk_count: int = Field(gt=0)
