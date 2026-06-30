"""RAG assistant schemas."""

from pydantic import BaseModel, Field


class RAGSourceReference(BaseModel):
    """Source metadata returned with grounded chat answers."""

    index: int
    document_id: str | None
    document_name: str
    document_type: str
    chunk_index: int
    score: float
    excerpt: str
    file_name: str | None = None


class RAGChatRequest(BaseModel):
    """Chat prompt payload for onboarding assistant."""

    question: str = Field(..., min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)
    session_id: str | None = Field(default=None, max_length=100)


class RAGChatResponse(BaseModel):
    """RAG assistant response with sources and session continuity."""

    answer: str
    session_id: str
    retrieved_chunks: int
    sources: list[RAGSourceReference]


class RAGSearchRequest(BaseModel):
    """Semantic search payload."""

    query: str = Field(..., min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)


class RAGSearchResult(BaseModel):
    """Semantic chunk hit."""

    content: str
    score: float
    document_id: str | None
    document_name: str | None
    document_type: str | None
    file_path: str | None
    chunk_index: int | None


class RAGDocumentResponse(BaseModel):
    """Uploaded or listed RAG document summary."""

    document_id: str
    document_name: str
    document_type: str
    file_path: str | None
    chunks_indexed: int | None = None
    file_size: int | None = None
    ingested_at: str | None = None


class RAGDeleteResponse(BaseModel):
    """Delete document status."""

    success: bool
    document_id: str
