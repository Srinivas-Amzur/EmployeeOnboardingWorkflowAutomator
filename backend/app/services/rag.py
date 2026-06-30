"""High-level RAG orchestration service."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from .ai_chat import AIChatService
from .document_processing import DocumentProcessingService
from .notification import NotificationService
from .vector_store import VectorStoreService
from ..schemas.notification import NotificationType


class RAGService:
    """Coordinates upload, indexing, retrieval, and grounded chat responses."""

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.document_service = DocumentProcessingService()
        self.vector_service = VectorStoreService()
        self.chat_service = AIChatService()
        self.notification_service = NotificationService(db) if db else None

    async def upload_document(
        self,
        user_id: UUID,
        upload_file: UploadFile,
        document_type: str,
    ) -> dict:
        payload = await self.document_service.process_upload(user_id, upload_file)
        chunk_count = self.vector_service.add_document_chunks(
            user_id=user_id,
            document_id=payload["document_id"],
            document_name=payload["document_name"],
            document_type=document_type,
            file_path=payload["file_path"],
            chunks=payload["chunks"],
        )
        if self.notification_service:
            await self.notification_service.create_ai_indexing_completed_notification(
                user_id=user_id,
                document_name=payload["document_name"],
                chunks_indexed=chunk_count,
            )
        return {
            "document_id": payload["document_id"],
            "document_name": payload["document_name"],
            "document_type": document_type,
            "file_path": payload["file_path"],
            "chunks_indexed": chunk_count,
            "file_size": payload["file_size"],
        }


    def semantic_search(self, user_id: UUID, query: str, top_k: int = 5) -> list[dict]:
        return self.vector_service.search(user_id, query, top_k=top_k)

    def answer_question(
        self,
        user_id: UUID,
        user_email: str,
        question: str,
        session_id: str | None,
        top_k: int,
    ) -> dict:
        results = self.semantic_search(user_id, question, top_k=top_k)
        effective_session_id = session_id or str(uuid4())

        if not results:
            return {
                "answer": "I could not find relevant onboarding context. Please upload onboarding policy documents or ask a narrower question.",
                "session_id": effective_session_id,
                "sources": [],
                "retrieved_chunks": 0,
            }

        context_lines = []
        sources = []
        for index, result in enumerate(results, start=1):
            source_name = result.get("document_name") or "Unknown document"
            excerpt = result.get("content", "")[:280]
            context_lines.append(f"[source {index}] {source_name}: {result.get('content', '')}")
            sources.append(
                {
                    "index": index,
                    "document_id": result.get("document_id"),
                    "document_name": source_name,
                    "document_type": result.get("document_type") or "general",
                    "chunk_index": result.get("chunk_index") or 0,
                    "score": result.get("score") or 0,
                    "excerpt": excerpt,
                    "file_name": Path(result.get("file_path") or "").name,
                }
            )

        context = "\n\n".join(context_lines)
        answer = self.chat_service.answer_with_context(
            user_email=user_email,
            session_id=f"{user_id}:{effective_session_id}",
            question=question,
            context=context,
        )

        return {
            "answer": answer,
            "session_id": effective_session_id,
            "sources": sources,
            "retrieved_chunks": len(results),
        }

    def list_documents(self, user_id: UUID) -> list[dict]:
        return self.vector_service.list_documents(user_id)

    def delete_document(self, user_id: UUID, document_id: str) -> bool:
        return self.vector_service.delete_document(user_id, document_id)

    async def log_ai_query(self, user_id: UUID, question: str) -> None:
        """Persist an AI assistant usage notification for auditability."""
        if not self.notification_service:
            return

        snippet = (question.strip().replace("\n", " "))[:140]
        await self.notification_service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.AI_ORCHESTRATION,
            title="AI query executed",
            message=f"Assistant query executed: {snippet}",
            payload={"audit_action": "ai_query_executed", "question": snippet},
            commit=True,
        )
