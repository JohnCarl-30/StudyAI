"""
Pinecone Vector Database Service
Replaces ChromaDB - works on Windows without C++ compiler!
"""
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Optional
import time

from app.config import settings


class PineconeService:

    def __init__(self):
        """Initialize Pinecone connection."""
        self.api_key = settings.PINECONE_API_KEY
        self.environment = settings.PINECONE_ENVIRONMENT
        self.index_name = settings.PINECONE_INDEX_NAME

        if not self.api_key:
            raise ValueError("PINECONE_API_KEY not found in environment")

        self.pc = Pinecone(api_key=self.api_key)

        self._ensure_index_exists()

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.OPENAI_API_KEY
        )

        print(f"✅ Pinecone initialized: index={self.index_name}")

    def _ensure_index_exists(self):
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            print(f"📝 Creating Pinecone index: {self.index_name}")

            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.environment
                )
            )

            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)

            print(f"✅ Index {self.index_name} created!")
        else:
            print(f"✅ Using existing index: {self.index_name}")

    def load_and_split_pdf(self, pdf_path: str) -> List[dict]:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = text_splitter.split_documents(documents)
        print(f"✂️  Created {len(chunks)} chunks")

        return chunks

    def embed_and_store(
        self,
        chunks: List[dict],
        user_id: int,
        document_id: int
    ) -> int:
        print(f"🧠 Generating embeddings and storing in Pinecone...")

        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "user_id": user_id,
                "document_id": document_id,
                "chunk_index": i
            })

        namespace = f"user_{user_id}"

        PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            index_name=self.index_name,
            namespace=namespace
        )

        print(f"✅ Stored {len(chunks)} vectors in Pinecone (namespace: {namespace})")
        return len(chunks)

    def search(
        self,
        query: str,
        user_id: int,
        document_id: Optional[int] = None,
        k: int = 4
    ) -> List[dict]:
        namespace = f"user_{user_id}"

        vector_store = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=namespace
        )

        filter_dict = None
        if document_id:
            filter_dict = {"document_id": {"$eq": document_id}}

        return vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )

    def delete_document_vectors(self, user_id: int, document_id: int):
        namespace = f"user_{user_id}"
        index = self.pc.Index(self.index_name)

        index.delete(
            filter={"document_id": {"$eq": document_id}},
            namespace=namespace
        )

        print(f"🗑️  Deleted vectors for document {document_id}")

    def get_chunk_count(self, user_id: int, document_id: int) -> int:
        namespace = f"user_{user_id}"
        index = self.pc.Index(self.index_name)

        stats = index.describe_index_stats()

        namespace_stats = stats.get('namespaces', {}).get(namespace, {})
        return namespace_stats.get('vector_count', 0)

    def get_vectorstore(self, user_id: int) -> PineconeVectorStore:
        namespace = f"user_{user_id}"

        return PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=namespace
        )
