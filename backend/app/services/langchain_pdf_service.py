
import os
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document as LangchainDocument
from pinecone import Pinecone
from app.config import settings


class LangChainPDFService:

    def __init__(self):
        # Embeddings model
        # Senior Tip: text-embedding-3-small is cheap ($0.02/1M tokens)
        # and good enough for educational content
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=settings.OPENAI_API_KEY
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,         # ~250 tokens per chunk
            chunk_overlap=200,       # Overlap to preserve context
            length_function=len,
            separators=[
                "\n\n",   # Try splitting on double newlines first (paragraphs)
                "\n",     # Then single newlines
                ". ",     # Then sentences
                " ",      # Then words
                ""        # Last resort: characters
            ]
        )

        # Initialize Pinecone client once and reuse the index connection
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self._index = pc.Index(settings.PINECONE_INDEX_NAME)

    def load_and_split_pdf(
        self,
        pdf_path: str,
        document_id: int,
        user_id: int
    ) -> List[LangchainDocument]:
        """
        Load PDF and split into chunks using LangChain.

        Args:
            pdf_path: Path to the PDF file
            document_id: Database ID for metadata
            user_id: User ID for metadata

        Returns:
            List of LangChain Document objects with metadata

        Senior Tip: We add metadata to each chunk so we can filter
        by document_id or user_id when searching later.
        """
        # Load PDF - LangChain handles extraction automatically
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()  # Returns list of Documents, one per page

        # Add our metadata to each page
        for page in pages:
            page.metadata.update({
                "document_id": document_id,
                "user_id": user_id,
            })

        chunks = self.text_splitter.split_documents(pages)

        return chunks

    def get_vectorstore(self, user_id: int) -> PineconeVectorStore:
      
        return PineconeVectorStore(
            index=self._index,
            embedding=self.embeddings,
            namespace=f"user_{user_id}"
        )

    def embed_and_store(
        self,
        chunks: List[LangchainDocument],
        user_id: int,
        document_id: int
    ) -> int:

        if not chunks:
            return 0

        vectorstore = self.get_vectorstore(user_id)
        vectorstore.add_documents(chunks)

        return len(chunks)

    def delete_document_vectors(
        self,
        user_id: int,
        document_id: int
    ) -> bool:

        try:
            # Pinecone supports metadata filtering on delete
            self._index.delete(
                filter={"document_id": document_id},
                namespace=f"user_{user_id}"
            )
            return True

        except Exception as e:
            print(f"Failed to delete vectors: {e}")
            return False

    def get_chunk_count(self, user_id: int, document_id: int) -> int:
        """Get number of vectors stored for a document."""
        try:
            # Query with a zero vector and metadata filter to count matches
            # text-embedding-3-small produces 1536-dimensional vectors
            results = self._index.query(
                vector=[0.0] * 1536,
                filter={"document_id": document_id},
                namespace=f"user_{user_id}",
                top_k=10000,
                include_values=False
            )
            return len(results.matches)
        except Exception:
            return 0
