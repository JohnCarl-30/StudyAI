"""
PDF processing service for text extraction.
Senior Tip: PDFs are tricky - try multiple libraries for best results.
"""
import os
from typing import List, Tuple
from pypdf import PdfReader
import pdfplumber


class PDFProcessor:
    """
    Handle PDF text extraction with fallback strategies.

    Senior Tips:
    - PyPDF2: Fast but sometimes misses formatting
    - pdfplumber: Better with tables and complex layouts
    - Always try multiple methods for best results
    """

    def __init__(self):
        pass

    @staticmethod
    def is_valid_pdf(file_path: str) -> bool:
        """
        Validate a PDF by checking its magic-byte header.
        Static because it needs no instance state.
        Senior Tip: Always validate before processing.
        """
        if not os.path.exists(file_path):
            return False
        try:
            with open(file_path, 'rb') as f:
                return f.read(5) == b'%PDF-'
        except Exception:
            return False

    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        try:
            text, pages = self._extract_with_pdfplumber(pdf_path)
            if text and len(text) > 100:  # Verify we got meaningful text
                return text, pages
        except Exception as e:
            print(f"pdfplumber failed: {e}, trying PyPDF2...")

        # Fallback to PyPDF2
        try:
            text, pages = self._extract_with_pypdf2(pdf_path)
            return text, pages
        except Exception as e:
            raise Exception(f"All PDF extraction methods failed: {e}")

    def extract_text_by_pages(
        self,
        pdf_path: str
    ) -> Tuple[List[Tuple[int, str]], int]:
        """
        Extract text page-by-page for better chunking.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of ([(page_num, text), ...], total_pages)

        Senior Tip: Page-aware extraction helps with citations.
        """
        page_texts = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    page_texts.append((i + 1, text))

                return page_texts, len(pdf.pages)

        except Exception as e:
            print(f"Page-by-page extraction failed: {e}")
            # Fallback: extract all at once
            text, pages = self.extract_text(pdf_path)
            return [(1, text)], pages

    def _extract_with_pdfplumber(self, pdf_path: str) -> Tuple[str, int]:
        """
        Extract using pdfplumber (handles tables better).

        Senior Tip: pdfplumber is slower but more accurate.
        """
        text_parts = []

        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)

            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

                # Extract tables for better formatting
                tables = page.extract_tables()
                for table in tables:
                    table_text = self._table_to_text(table)
                    text_parts.append(table_text)

        full_text = "\n\n".join(text_parts)
        return full_text, page_count

    def _extract_with_pypdf2(self, pdf_path: str) -> Tuple[str, int]:
        """
        Extract using PyPDF2 (faster but simpler).

        Senior Tip: PyPDF2 is faster for simple documents.
        """
        text_parts = []

        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            page_count = len(reader.pages)

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        full_text = "\n\n".join(text_parts)
        return full_text, page_count

    def _table_to_text(self, table: List[List[str]]) -> str:
        """
        Convert table data to readable text.

        Senior Tip: Tables need special formatting to be useful in text.
        """
        if not table:
            return ""

        lines = []
        for row in table:
            row_text = " | ".join(str(cell) if cell else "" for cell in row)
            lines.append(row_text)

        return "\n".join(lines)

    def get_pdf_metadata(self, pdf_path: str) -> dict:
        """
        Extract PDF metadata.

        Returns:
            Dictionary with title, author, page_count, etc.
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata = pdf.metadata or {}
                return {
                    "title": metadata.get("Title", ""),
                    "author": metadata.get("Author", ""),
                    "page_count": len(pdf.pages),
                    "creator": metadata.get("Creator", ""),
                }
        except Exception:
            return {"page_count": 0}


# Backward-compatible alias — callers importing is_valid_pdf directly continue to work
def is_valid_pdf(file_path: str) -> bool:
    return PDFProcessor.is_valid_pdf(file_path)
