from typing import List, Optional, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument


class TextChunker:
    """
    Text chunker using LangChain's RecursiveCharacterTextSplitter.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        # LangChain splitter - tries these s eparators in order
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",   # 1st: paragraphs
                "\n",     # 2nd: lines
                ". ",     # 3rd: sentences
                " ",      # 4th: words
                "",       # last resort: characters
            ]
        )

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        if len(text) < self.min_chunk_size:
            return [text]
        return self._splitter.split_text(text)

    def chunk_documents(
        self,
        documents: List[LangchainDocument]
    ) -> List[LangchainDocument]:
        """Split LangChain Documents while preserving metadata."""
        return self._splitter.split_documents(documents)

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate (1 token ≈ 4 chars)."""
        return len(text) // 4


class PageAwareChunker(TextChunker):
    """
    Chunker that tracks which page each chunk came from.

    Senior Tip: Page numbers let you cite sources later:
    "This answer is from page 3 of your document."
    """

    def chunk_with_pages(
        self,
        page_texts: List[Tuple[int, str]]
    ) -> List[Tuple[str, Optional[int]]]:
        """
        Split text while preserving page numbers.

        Args:
            page_texts: List of (page_number, text) tuples

        Returns:
            List of (chunk_text, page_number) tuples

        Example:
            Input:  [(1, "Page 1 text..."), (2, "Page 2 text...")]
            Output: [("chunk 1", 1), ("chunk 2", 1), ("chunk 3", 2)]
        """
        chunks_with_pages = []

        for page_num, page_text in page_texts:
            if not page_text or not page_text.strip():
                continue  # Skip empty pages

            chunks = self.chunk_text(page_text)

            for chunk in chunks:
                if chunk.strip():  # Skip empty chunks
                    chunks_with_pages.append((chunk, page_num))

        return chunks_with_pages

    def chunk_langchain_docs(
        self,
        documents: List[LangchainDocument]
    ) -> List[LangchainDocument]:
        """
        Chunk LangChain Documents preserving ALL metadata including page numbers.
        Use this when storing to ChromaDB.
        """
        return self._splitter.split_documents(documents)




