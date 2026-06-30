"""Compatibility wrapper around service-layer RAG implementation."""

from __future__ import annotations

from ..services.rag import RAGService


_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """Return singleton RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
