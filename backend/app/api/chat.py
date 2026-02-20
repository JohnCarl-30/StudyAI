from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.models.user import User
from app.models.document import ProcessingStatus
from app.api.deps import get_current_user, get_document_service, get_rag_service
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceDocument,
    GenerateFlashcardsRequest,
    SearchRequest,
    SearchResult
)
from app.services.rag_services import RAGService
from app.services.document_service import DocumentService

router = APIRouter(prefix="/chat", tags=["Chat & RAG"])


@router.post("/ask", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
    rag_service: RAGService = Depends(get_rag_service),
):
    if request.document_id:
        document = doc_service.get_document(request.document_id, current_user.id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        if document.status != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document is not ready. Status: {document.status}"
            )

    try:
        chat_history = []
        if request.chat_history:
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.chat_history
            ]

        result = rag_service.ask_question(
            question=request.question,
            user_id=current_user.id,
            document_id=request.document_id,
            chat_history=chat_history,
            query_mode=request.query_mode.value
        )

        sources = [
            SourceDocument(
                content=src["content"],
                page=str(src.get("page", "unknown")),
                document_id=src.get("document_id")
            )
            for src in result["sources"]
        ]

        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            query_mode=result["query_mode"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )


@router.post("/generate-flashcards")
def generate_flashcards(
    request: GenerateFlashcardsRequest,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
    rag_service: RAGService = Depends(get_rag_service),
):
    document = doc_service.get_document(request.document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    if document.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document not ready. Status: {document.status}"
        )

    try:
        flashcards = rag_service.generate_flashcards(
            user_id=current_user.id,
            document_id=request.document_id,
            topic=request.topic,
            num_cards=request.num_cards,
            difficulty=request.difficulty
        )
        return {
            "document_id": request.document_id,
            "topic": request.topic,
            "flashcards": flashcards,
            "count": len(flashcards)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(e)}"
        )


@router.post("/search", response_model=List[SearchResult])
def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    try:
        results = rag_service.search_documents(
            query=request.query,
            user_id=current_user.id,
            document_id=request.document_id,
            k=request.k
        )
        return [
            SearchResult(
                content=r["content"],
                page=str(r.get("page", "unknown")),
                document_id=r.get("document_id")
            )
            for r in results
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/history/{document_id}")
def get_suggested_questions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    document = doc_service.get_document(document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return {
        "document_id": document_id,
        "document_title": document.title,
        "suggested_questions": [
            f"What are the main topics in {document.title}?",
            f"Summarize the key concepts in {document.title}",
            f"What are the most important points to remember?",
            f"Create practice problems from {document.title}",
            f"Explain the most complex concept in simple terms"
        ]
    }
