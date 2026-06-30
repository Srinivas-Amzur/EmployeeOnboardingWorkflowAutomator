"""LCEL chain builders for RAG chat responses."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser


def build_rag_response_chain(llm):
    """Build LCEL response chain: prompt | llm | parser."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are an onboarding policy assistant for an enterprise HR platform.
Answer only using the provided context.
If the answer is not present in context, say that clearly and suggest uploading relevant onboarding documentation.
Keep responses concise, factual, and operational.
Always mention source citations in the format [source N] when context supports the answer.

Context:
{context}
""".strip(),
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ]
    )
    return prompt | llm | StrOutputParser()
