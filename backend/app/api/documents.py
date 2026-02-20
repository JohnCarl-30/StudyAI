from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import List

from app.models.user import User
from app.api.deps import get_current_user, get_document_service
from app.schemas.document import (
    DocumentResponse,
    DocumentWithContent,
    DocumentUpdate,
    ChunkResponse
)
from app.services.document_service import DocumentService
from app.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = None,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the maximum limit")

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        file_path, file_size = DocumentService.save_upload_file(file, current_user.id)

        document = doc_service.create_document(
            user=current_user,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            title=title
        )

        try:
            document = doc_service.process_document(document.id)
        except Exception as e:
            print(f"Error processing document {document.id}: {str(e)}")

        return document
    except Exception as e:
        print(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    return doc_service.get_user_documents(
        user_id=current_user.id,
        skip=skip,
        limit=min(limit, 100)
    )


@router.get("/{document_id}", response_model=DocumentWithContent)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    document = doc_service.get_document(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/content", response_model=DocumentWithContent)
def get_document_content(
    document_id: int,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """
    Get document with full extracted text.

    Senior Tip: Separate endpoint for content to avoid large payloads on list.
    """
    document = doc_service.get_document(document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """
    Delete a document and its file.

    Senior Tip: Return 204 No Content for successful DELETE.
    """
    deleted = doc_service.delete_document(document_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return None


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
def reprocess_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """
    Reprocess a document (if extraction failed).

    Use case: Retry failed processing or update chunking strategy.
    """
    document = doc_service.get_document(document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    try:
        return doc_service.process_document(document_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess document: {str(e)}"
        )
