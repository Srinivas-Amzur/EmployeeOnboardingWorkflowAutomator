"""Centralized LiteLLM-backed model and embedding initialization."""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from ..core.config import get_settings

settings = get_settings()


def get_llm(
    model: str = "gemini/gemini-2.5-flash",
    temperature: float = 0.7,
    user_email: str | None = None,
) -> ChatOpenAI:
    """
    Get LLM instance configured with LiteLLM proxy.

    This is the ONLY way to instantiate an LLM in the application.

    Args:
        model: Model identifier (e.g., "gemini/gemini-2.5-flash", "gpt-4o")
        temperature: Temperature parameter (0-1)
        user_email: User context propagated to LiteLLM for traceability

    Returns:
        ChatOpenAI instance configured with LiteLLM proxy
    """
    model_kwargs = {"user": user_email} if user_email else {}

    return ChatOpenAI(
        model=model,
        api_key=settings.LITELLM_API_KEY,
        base_url=settings.LITELLM_PROXY_URL,
        temperature=temperature,
        timeout=60,
        model_kwargs=model_kwargs,
    )


def get_fast_llm(temperature: float = 0.5, user_email: str | None = None) -> ChatOpenAI:
    """
    Get a fast LLM instance for quick responses.

    Args:
        temperature: Temperature parameter

    Returns:
        ChatOpenAI instance with fast model
    """
    return get_llm(model="gemini/gemini-2.5-flash", temperature=temperature, user_email=user_email)


def get_advanced_llm(temperature: float = 0.3, user_email: str | None = None) -> ChatOpenAI:
    """
    Get an advanced LLM instance for complex reasoning.

    Args:
        temperature: Temperature parameter

    Returns:
        ChatOpenAI instance with advanced model
    """
    return get_llm(model="gpt-4o", temperature=temperature, user_email=user_email)


def get_embeddings() -> OpenAIEmbeddings:
    """Get embedding client configured against LiteLLM proxy."""
    return OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=settings.LITELLM_API_KEY,
        base_url=settings.LITELLM_PROXY_URL,
    )
