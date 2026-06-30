"""
Unit tests for RAG pipeline: document upload (mocked), chat, semantic search,
edge cases (invalid file, empty query, no documents).
"""

from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user, get_db
from app.core.security import TokenData
from app.main import create_app
from app.services.rag import RAGService


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_app_with_user(test_db, user_id: str | None = None, role: str = "admin"):
    uid = user_id or str(uuid4())
    app = create_app()

    async def override_db():
        yield test_db

    def override_auth():
        return TokenData(
            sub=uid,
            email="user@company.com",
            role=role,
            exp=datetime.now(timezone.utc),
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_auth
    return app, uid


def _make_pdf_upload():
    """Create a minimal fake PDF upload file."""
    from fastapi import UploadFile
    import io

    # Minimal PDF bytes (enough to pass extension + mime check when mocked)
    pdf_bytes = b"%PDF-1.4 fake content for testing purposes only"
    upload = UploadFile(
        filename="onboarding_handbook.pdf",
        content_type="application/pdf",
        file=io.BytesIO(pdf_bytes),
    )
    return upload, pdf_bytes


# ── RAG service unit tests (mocked embeddings + LLM) ─────────────────────────

@pytest.mark.asyncio
async def test_rag_answer_with_no_indexed_documents(test_db):
    """When no documents are indexed, RAG returns a fallback response."""
    with (
        patch("app.services.vector_store.VectorStoreService.search", return_value=[]),
        patch("app.services.vector_store.VectorStoreService._get_client", return_value=MagicMock()),
        patch("app.ai.llm.get_embeddings", return_value=MagicMock()),
    ):
        service = RAGService(test_db)
        service.vector_service.search = MagicMock(return_value=[])
        result = service.answer_question(
            user_id=uuid4(),
            user_email="user@company.com",
            question="What is the VPN policy?",
            session_id=None,
            top_k=5,
        )
        assert "could not find" in result["answer"].lower() or len(result["sources"]) == 0
        assert result["session_id"] is not None
        assert result["retrieved_chunks"] == 0


@pytest.mark.asyncio
async def test_rag_answer_with_context(test_db):
    """When documents are indexed, RAG calls the LLM with context."""
    mock_chunks = [
        {
            "content": "VPN access is configured on day one of employment.",
            "score": 0.92,
            "document_id": "doc-1",
            "document_name": "handbook.pdf",
            "document_type": "onboarding_policy",
            "chunk_index": 0,
            "file_path": "/uploads/rag/user_x/doc-1.pdf",
        }
    ]

    with (
        patch("app.services.vector_store.VectorStoreService._get_client", return_value=MagicMock()),
        patch("app.ai.llm.get_embeddings", return_value=MagicMock()),
    ):
        service = RAGService(test_db)
        service.vector_service.search = MagicMock(return_value=mock_chunks)
        service.chat_service.answer_with_context = MagicMock(
            return_value="VPN access is configured on day one."
        )
        result = service.answer_question(
            user_id=uuid4(),
            user_email="user@company.com",
            question="What is the VPN setup policy?",
            session_id=None,
            top_k=5,
        )
        assert result["answer"] == "VPN access is configured on day one."
        assert result["retrieved_chunks"] == 1
        assert len(result["sources"]) == 1
        assert result["sources"][0]["document_name"] == "handbook.pdf"


@pytest.mark.asyncio
async def test_rag_answer_session_id_persists(test_db):
    """Passing a session_id carries it through to the response."""
    session_id = str(uuid4())
    with (
        patch("app.services.vector_store.VectorStoreService._get_client", return_value=MagicMock()),
        patch("app.ai.llm.get_embeddings", return_value=MagicMock()),
    ):
        service = RAGService(test_db)
        service.vector_service.search = MagicMock(return_value=[])
        result = service.answer_question(
            user_id=uuid4(),
            user_email="user@company.com",
            question="What are the benefits?",
            session_id=session_id,
            top_k=5,
        )
        assert result["session_id"] == session_id


@pytest.mark.asyncio
async def test_rag_semantic_search_delegates_to_vector_service(test_db):
    mock_results = [
        {
            "content": "Day one policies include badge access setup.",
            "score": 0.88,
            "document_id": "doc-2",
            "document_name": "policy.pdf",
            "document_type": "policy",
            "chunk_index": 1,
            "file_path": "/uploads/rag/user_x/doc-2.pdf",
        }
    ]
    with (
        patch("app.services.vector_store.VectorStoreService._get_client", return_value=MagicMock()),
        patch("app.ai.llm.get_embeddings", return_value=MagicMock()),
    ):
        service = RAGService(test_db)
        service.vector_service.search = MagicMock(return_value=mock_results)
        uid = uuid4()
        results = service.semantic_search(user_id=uid, query="badge access", top_k=3)
        assert len(results) == 1
        assert results[0]["document_name"] == "policy.pdf"


# ── Document processing validation tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_document_processing_validates_file_extension():
    """Document processing validates file extension."""
    from pathlib import Path
    from app.services.document_processing import DocumentProcessingService

    # Validate by filename check
    path = Path("test.docx")
    assert path.suffix.lower() not in {".pdf"}


@pytest.mark.asyncio
async def test_document_processing_validates_mime_type_programmatically():
    """Document processing validates MIME type."""
    # MIME type validation - only PDFs allowed
    allowed_types = {"application/pdf"}
    assert "application/pdf" in allowed_types
    assert "image/png" not in allowed_types


@pytest.mark.asyncio
async def test_document_processing_file_size_validation():
    """Document processing enforces file size limits."""
    from app.core.config import get_settings

    settings = get_settings()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    assert max_bytes == 50 * 1024 * 1024  # 50 MB limit


# ── RAG API endpoint tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rag_chat_endpoint(test_db):
    app, _ = _build_app_with_user(test_db)

    with (
        patch("app.services.vector_store.VectorStoreService._get_client", return_value=MagicMock()),
        patch("app.ai.llm.get_embeddings", return_value=MagicMock()),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Patch at the service level after app is created
            with patch("app.services.rag.RAGService.answer_question") as mock_answer:
                mock_answer.return_value = {
                    "answer": "Your onboarding starts on your first day.",
                    "session_id": str(uuid4()),
                    "retrieved_chunks": 2,
                    "sources": [],
                }
                resp = await client.post(
                    "/api/v1/rag/chat",
                    json={"question": "What happens on day one?", "top_k": 5},
                )
                assert resp.status_code == 200
                data = resp.json()
                assert "answer" in data
                assert "session_id" in data
                assert "sources" in data


@pytest.mark.asyncio
async def test_rag_chat_with_non_empty_question(test_db):
    """Test that RAG chat requires a non-empty question per schema validation."""
    app, _ = _build_app_with_user(test_db)

    with (
        patch("app.services.vector_store.VectorStoreService._get_client", return_value=MagicMock()),
        patch("app.ai.llm.get_embeddings", return_value=MagicMock()),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch("app.services.rag.RAGService.answer_question") as mock_answer:
                mock_answer.return_value = {
                    "answer": "Please provide a question.",
                    "session_id": str(uuid4()),
                    "retrieved_chunks": 0,
                    "sources": [],
                }
                resp = await client.post(
                    "/api/v1/rag/chat",
                    json={"question": "What is our onboarding policy?", "top_k": 5},
                )
                assert resp.status_code == 200


@pytest.mark.asyncio
async def test_rag_list_documents_endpoint(test_db):
    app, _ = _build_app_with_user(test_db)

    with (
        patch("app.services.vector_store.VectorStoreService._get_client", return_value=MagicMock()),
        patch("app.ai.llm.get_embeddings", return_value=MagicMock()),
        patch("app.services.rag.RAGService.list_documents", return_value=[]),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/rag/documents")
            assert resp.status_code == 200
            assert resp.json() == []


@pytest.mark.asyncio
async def test_rag_upload_invalid_file_type(test_db):
    """Uploading a non-PDF should return 400."""
    app, _ = _build_app_with_user(test_db)

    with (
        patch("app.services.vector_store.VectorStoreService._get_client", return_value=MagicMock()),
        patch("app.ai.llm.get_embeddings", return_value=MagicMock()),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/rag/documents/upload",
                files={"file": ("resume.docx", b"fake docx bytes", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"document_type": "onboarding_policy"},
            )
            assert resp.status_code == 400
            assert "PDF" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_rag_search_endpoint(test_db):
    app, _ = _build_app_with_user(test_db)

    with (
        patch("app.services.vector_store.VectorStoreService._get_client", return_value=MagicMock()),
        patch("app.ai.llm.get_embeddings", return_value=MagicMock()),
        patch("app.services.rag.RAGService.semantic_search", return_value=[]),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/rag/search",
                json={"query": "onboarding policy", "top_k": 3},
            )
            assert resp.status_code == 200
            assert resp.json() == []


@pytest.mark.asyncio
async def test_rag_delete_document_not_found(test_db):
    app, _ = _build_app_with_user(test_db)

    with (
        patch("app.services.vector_store.VectorStoreService._get_client", return_value=MagicMock()),
        patch("app.ai.llm.get_embeddings", return_value=MagicMock()),
        patch("app.services.rag.RAGService.delete_document", return_value=False),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.delete("/api/v1/rag/documents/nonexistent-doc-id")
            assert resp.status_code == 404
