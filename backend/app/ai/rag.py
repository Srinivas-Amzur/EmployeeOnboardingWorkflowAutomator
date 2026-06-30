"""Low-level RAG helpers shared by higher-level services."""

from chromadb import HttpClient

from ..core.config import get_settings
from .llm import get_embeddings as _get_embeddings_client

settings = get_settings()


def get_chromadb_client() -> HttpClient:
    """
    Get ChromaDB HTTP client.

    Returns:
        ChromaDB client instance
    """
    return HttpClient(host=settings.CHROMADB_HOST, port=settings.CHROMADB_PORT)


def get_embeddings():
    """
    Get embeddings model configured with LiteLLM.

    Returns:
        OpenAIEmbeddings instance
    """
    return _get_embeddings_client()


def get_user_collection_name(user_id: str) -> str:
    """
    Get collection name for user.

    Collection strategy: user_{user_id}

    Args:
        user_id: User UUID

    Returns:
        Collection name
    """
    return f"user_{user_id}"


__all__ = ["get_chromadb_client", "get_embeddings", "get_user_collection_name"]
