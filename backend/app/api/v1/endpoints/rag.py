"""RAG assistant API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ....core.security import TokenData
from ....schemas import (
    RAGChatRequest,
    RAGChatResponse,
    RAGDeleteResponse,
    RAGDocumentResponse,
    RAGSearchRequest,
    RAGSearchResult,
)
from ....services.rag import RAGService
from ...dependencies import DbSession, get_current_user

router = APIRouter(tags=["rag"], prefix="/rag")


def get_rag_service(db: DbSession) -> RAGService:
    """Dependency to resolve RAG service."""
    return RAGService(db)


@router.post("/documents/upload", response_model=RAGDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_rag_document(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    file: UploadFile = File(...),
    document_type: str = Form(default="onboarding_policy"),
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGDocumentResponse:
    """Upload and index an onboarding PDF into user-isolated Chroma collection."""
    try:
        payload = await rag_service.upload_document(
            user_id=UUID(current_user.sub),
            upload_file=file,
            document_type=document_type,
        )
        return RAGDocumentResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/chat", response_model=RAGChatResponse)
async def chat_with_onboarding_assistant(
    request: RAGChatRequest,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGChatResponse:
    """Get contextual onboarding answer with source citations."""
    user_id = UUID(current_user.sub)
    payload = rag_service.answer_question(
        user_id=user_id,
        user_email=current_user.email,
        question=request.question,
        session_id=request.session_id,
        top_k=request.top_k,
    )
    await rag_service.log_ai_query(user_id=user_id, question=request.question)
    return RAGChatResponse(**payload)


@router.post("/search", response_model=list[RAGSearchResult])
async def semantic_search_documents(
    request: RAGSearchRequest,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    rag_service: RAGService = Depends(get_rag_service),
) -> list[RAGSearchResult]:
    """Run semantic retrieval over onboarding docs."""
    results = rag_service.semantic_search(
        user_id=UUID(current_user.sub),
        query=request.query,
        top_k=request.top_k,
    )
    return [RAGSearchResult(**result) for result in results]


@router.get("/documents", response_model=list[RAGDocumentResponse])
async def list_rag_documents(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    rag_service: RAGService = Depends(get_rag_service),
) -> list[RAGDocumentResponse]:
    """List indexed onboarding documents for current user."""
    documents = rag_service.list_documents(user_id=UUID(current_user.sub))
    return [RAGDocumentResponse(**doc) for doc in documents]


@router.delete("/documents/{document_id}", response_model=RAGDeleteResponse)
async def delete_rag_document(
    document_id: str,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGDeleteResponse:
    """Delete indexed document chunks from user collection."""
    success = rag_service.delete_document(user_id=UUID(current_user.sub), document_id=document_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return RAGDeleteResponse(success=True, document_id=document_id)
