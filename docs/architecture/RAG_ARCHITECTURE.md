# RAG Architecture

# Overview

The platform supports AI-powered onboarding document search using RAG.

RAG enables:
- onboarding policy Q&A
- handbook search
- contextual AI responses

---

# Document Types

Supported:
- employee handbooks
- policies
- compliance PDFs
- onboarding guides

---

# RAG Pipeline

1. upload document
2. extract content
3. chunk document
4. create embeddings
5. store in ChromaDB
6. retrieve context
7. generate AI response

---

# Embeddings

Model:
text-embedding-3-large

Access:
LiteLLM proxy only

---

# Vector Store

Technology:
ChromaDB

Collection Strategy:
user_{user_id}

---

# Retrieval Flow

User Question
↓
Embedding Generation
↓
Semantic Search
↓
Relevant Chunks Retrieved
↓
LLM Response Generation

---

# Security Rules

- isolated user collections
- secure document access
- no cross-user retrieval

---

# AI Response Rules

Responses:
- contextual
- grounded in retrieved documents
- include sources where possible