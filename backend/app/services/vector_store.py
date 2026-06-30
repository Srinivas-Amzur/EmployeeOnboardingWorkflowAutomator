"""ChromaDB vector storage and retrieval service."""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import chromadb
from chromadb.api.models.Collection import Collection

from ..ai.llm import get_embeddings
from ..core.config import get_settings

settings = get_settings()


class VectorStoreService:
    """Handles embedding storage and semantic retrieval in ChromaDB."""

    def __init__(self) -> None:
        self.embeddings = get_embeddings()
        self.client = self._get_client()

    def _get_client(self):
        try:
            client = chromadb.HttpClient(host=settings.CHROMADB_HOST, port=settings.CHROMADB_PORT)
            client.heartbeat()  # probe — raises if no HTTP server is running
            return client
        except Exception:
            persist_path = str(Path(settings.UPLOAD_DIR) / "chroma")
            return chromadb.PersistentClient(path=persist_path)

    def _collection_name(self, user_id: UUID) -> str:
        return f"user_{user_id}"

    def _get_collection(self, user_id: UUID) -> Collection:
        return self.client.get_or_create_collection(name=self._collection_name(user_id))

    def add_document_chunks(
        self,
        user_id: UUID,
        document_id: str,
        document_name: str,
        document_type: str,
        file_path: str,
        chunks: list[str],
    ) -> int:
        """Embed and store chunks for one document."""
        collection = self._get_collection(user_id)
        chunk_ids = [f"{document_id}_chunk_{index}" for index in range(len(chunks))]
        embeddings = self.embeddings.embed_documents(chunks)
        timestamp = datetime.now(timezone.utc).isoformat()

        metadatas = [
            {
                "document_id": document_id,
                "document_name": document_name,
                "document_type": document_type,
                "file_path": file_path,
                "chunk_index": index,
                "ingested_at": timestamp,
            }
            for index in range(len(chunks))
        ]

        collection.add(
            ids=chunk_ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def search(self, user_id: UUID, query: str, top_k: int = 5) -> list[dict]:
        """Run semantic search and return scored chunks with metadata."""
        collection = self._get_collection(user_id)
        query_embedding = self.embeddings.embed_query(query)
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        formatted: list[dict] = []
        for index, content in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else 0.0
            score = 1 / (1 + float(distance))
            formatted.append(
                {
                    "content": content,
                    "score": round(score, 4),
                    "document_id": metadata.get("document_id"),
                    "document_name": metadata.get("document_name"),
                    "document_type": metadata.get("document_type"),
                    "file_path": metadata.get("file_path"),
                    "chunk_index": metadata.get("chunk_index"),
                }
            )
        return formatted

    def list_documents(self, user_id: UUID) -> list[dict]:
        """List distinct uploaded documents for a user collection."""
        collection = self._get_collection(user_id)
        result = collection.get(include=["metadatas"])
        metadatas = result.get("metadatas", [])

        grouped: "OrderedDict[str, dict]" = OrderedDict()
        for metadata in metadatas:
            document_id = metadata.get("document_id")
            if not document_id:
                continue
            if document_id not in grouped:
                grouped[document_id] = {
                    "document_id": document_id,
                    "document_name": metadata.get("document_name"),
                    "document_type": metadata.get("document_type"),
                    "file_path": metadata.get("file_path"),
                    "ingested_at": metadata.get("ingested_at"),
                }
        return list(grouped.values())

    def delete_document(self, user_id: UUID, document_id: str) -> bool:
        """Delete all chunks of a document from user collection."""
        collection = self._get_collection(user_id)
        existing = collection.get(where={"document_id": document_id})
        ids = existing.get("ids", []) if existing else []
        if not ids:
            return False
        collection.delete(ids=ids)
        return True
