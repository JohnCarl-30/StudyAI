"""
Document service - business logic for document management.
Senior Tip: Services contain business logic, keep routes thin.
"""
import os
import shutil
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.document import Document, ProcessingStatus
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services.pdf_service import PDFProcessor
from app.utils.chunking import PageAwareChunker
from app.config import settings


class DocumentService:

    def __init__(self, db: Session):
        self.db = db
        self.pdf_processor = PDFProcessor()
        self.chunker = PageAwareChunker(
            chunk_size=1000,
            chunk_overlap=200
        )

    @staticmethod
    def save_upload_file(upload_file, user_id: int) -> tuple[str, int]:
        """
        Save an uploaded file to disk, organized by user_id.
        Static because it needs no database access.

        Returns:
            (file_path, file_size)

        Senior Tip: Organize files by user_id to avoid conflicts.
        """
        upload_dir = os.path.join(settings.UPLOAD_DIRECTORY, str(user_id))
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{upload_file.filename}"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        file_size = os.path.getsize(file_path)

        return file_path, file_size

    def create_document(
        self,
        user: User,
        filename: str,
        file_path: str,
        file_size: int,
        title: Optional[str] = None
    ) -> Document:
        document = Document(
            user_id=user.id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            title=title or filename,
            status=ProcessingStatus.PENDING
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def process_document(self, document_id: int) -> Document:
        document = self.db.query(Document).filter(
            Document.id == document_id
        ).first()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        document.status = ProcessingStatus.PROCESSING
        self.db.commit()

        try:
            if not PDFProcessor.is_valid_pdf(document.file_path):
                raise Exception("Invalid PDF file")

            page_texts, page_count = self.pdf_processor.extract_text_by_pages(
                document.file_path
            )

            full_text = "\n\n".join([text for _, text in page_texts])

            chunks_with_pages = self.chunker.chunk_with_pages(page_texts)

            for idx, (chunk_text, page_num) in enumerate(chunks_with_pages):
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    content=chunk_text,
                    page_number=page_num
                )
                self.db.add(chunk)

            document.extracted_text = full_text
            document.page_count = page_count
            document.chunk_count = len(chunks_with_pages)
            document.status = ProcessingStatus.COMPLETED
            document.processed_at = datetime.utcnow()
            document.processing_error = None

            self.db.commit()
            self.db.refresh(document)

            return document

        except Exception as e:
            document.status = ProcessingStatus.FAILED
            document.processing_error = str(e)
            self.db.commit()

            raise Exception(f"Failed to process document: {e}")

    def get_user_documents(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Document]:
        """
        Get all documents for a user with pagination.

        Senior Tip: Always paginate list endpoints.
        """
        return self.db.query(Document).filter(
            Document.user_id == user_id
        ).offset(skip).limit(limit).all()

    def get_document(self, document_id: int, user_id: int) -> Optional[Document]:
        """
        Get a specific document if user owns it.

        Senior Tip: Always verify ownership in services.
        """
        return self.db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()

    def get_document_chunks(
        self,
        document_id: int,
        user_id: int
    ) -> List[DocumentChunk]:
        """
        Get all chunks for a document.

        Senior Tip: Verify user owns document before returning chunks.
        """
        document = self.get_document(document_id, user_id)
        if not document:
            return []

        return self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()

    def delete_document(self, document_id: int, user_id: int) -> bool:
        """
        Delete document and its file.

        Returns:
            True if deleted, False if not found

        Senior Tip: Clean up files and database records.
        """
        document = self.get_document(document_id, user_id)
        if not document:
            return False

        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            print(f"Failed to delete file: {e}")

        self.db.delete(document)
        self.db.commit()

        return True

    def update_document_title(
        self,
        document_id: int,
        user_id: int,
        new_title: str
    ) -> Optional[Document]:
        """Update document title."""
        document = self.get_document(document_id, user_id)
        if not document:
            return None

        document.title = new_title
        self.db.commit()
        self.db.refresh(document)

        return document


# Backward-compatible alias — api/documents.py imports this name directly
save_upload_file = DocumentService.save_upload_file
