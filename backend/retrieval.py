"""CrewAI documentation retrieval tool with per-run source logging."""

from collections.abc import Sequence

from crewai.tools import BaseTool, tool

from rag.index import ChromaRetriever
from rag.models import RetrievalEvent


def build_retrieval_tools(
    retriever: ChromaRetriever,
    event_log: list[RetrievalEvent],
    *,
    result_limit: int = 3,
) -> Sequence[BaseTool]:
    @tool("search_official_documentation")
    def search_official_documentation(query: str) -> str:
        """Search pinned official API documentation and return cited excerpts."""
        results = retriever.retrieve(query, result_limit)
        event_log.append(RetrievalEvent(query=query.strip(), results=results))
        sections = []
        for result in results:
            sections.append(
                f"SOURCE: {result.source_id} | {result.library} "
                f"{result.library_version} | {result.title} / {result.heading}\n"
                f"URL: {result.source_url}\n{result.content}"
            )
        return "\n\n".join(sections)

    return [search_official_documentation]
