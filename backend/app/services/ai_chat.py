"""AI chat service for contextual onboarding responses."""

from __future__ import annotations

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from ..ai.chains.rag_chain import build_rag_response_chain
from ..ai.llm import get_fast_llm


class AIChatService:
    """Runs retrieval-grounded chat responses with session memory."""

    def __init__(self) -> None:
        self._history_store: dict[str, ChatMessageHistory] = {}

    def _get_session_history(self, session_id: str) -> ChatMessageHistory:
        history = self._history_store.get(session_id)
        if history is None:
            history = ChatMessageHistory()
            self._history_store[session_id] = history
        return history

    def answer_with_context(
        self,
        user_email: str,
        session_id: str,
        question: str,
        context: str,
    ) -> str:
        """Generate one grounded response from context and prior turns."""
        llm = get_fast_llm(temperature=0.2, user_email=user_email)
        chain = build_rag_response_chain(llm)

        conversational_chain = RunnableWithMessageHistory(
            chain,
            self._get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )

        response = conversational_chain.invoke(
            {
                "question": question,
                "context": context,
            },
            config={"configurable": {"session_id": session_id}},
        )
        return str(response)
