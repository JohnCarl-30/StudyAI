
from typing import List, Optional, AsyncGenerator
from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAIEmbeddings
from app.services.pinecone_service import PineconeService

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory       
from langchain.prompts import PromptTemplate                 
from langchain_core.messages import HumanMessage, AIMessage  
from app.config import settings



STUDY_QA_PROMPT = PromptTemplate(
    template="""You are an expert study assistant helping a student understand their study materials.

Use the following excerpts from their uploaded documents to answer the question.
If you cannot find the answer in the documents, say so clearly.
Always cite which part of the document your answer comes from.

Context from documents:
{context} 

Previous conversation:
{chat_history}

Student's question: {question}

Instructions:
- Answer clearly and educationally
- If asked to explain simply, use analogies and examples
- If asked for practice problems, create relevant questions
- Always reference the source material
- If the answer isn't in the documents, say "I couldn't find this in your documents, but..."

Answer:""",
    input_variables=["context", "chat_history", "question"]
)

FLASHCARD_PROMPT = PromptTemplate(
    template="""You are an expert educator creating flashcards from study materials.

Based on the following content from a student's document, generate {num_cards} flashcards.

Document content:
{context}

Topic focus (if specified): {topic}

Requirements:
- Each flashcard should test ONE specific concept
- Questions should be clear and unambiguous  
- Answers should be concise but complete
- Include a mix of: definitions, concepts, applications, comparisons
- Difficulty: {difficulty}

Return ONLY a JSON array in this exact format:
[
  {{
    "question": "What is...?",
    "answer": "It is...",
    "difficulty": "easy|medium|hard"
  }}
]

JSON:""",
    input_variables=["context", "num_cards", "topic", "difficulty"]
)



class RAGService:


    def __init__(self):

        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.3,
            max_tokens=2048
        )

        self.flashcard_llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.5,
            max_tokens=4096
        )

        import httpx
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=settings.OPENAI_API_KEY,
            http_client=httpx.Client(),
            http_async_client=httpx.AsyncClient()
        )

        # Initialize once and reuse — creating PineconeService on every
        # request caused _ensure_index_exists() to run on each call,
        # making requests timeout and CORS headers never arrive.
        self._pinecone = PineconeService()

    def get_vectorstore(self, user_id: int):
        return self._pinecone.get_vectorstore(user_id)

    def get_retriever(
        self,
        user_id: int,
        document_id: Optional[int] = None,
        k: int = 5
    ):

        vectorstore = self.get_vectorstore(user_id)

        
        search_kwargs = {"k": k}

        if document_id:
            search_kwargs["filter"] = {"document_id": document_id}

        retriever = vectorstore.as_retriever(
            search_type="similarity",   # Semantic similarity search
            search_kwargs=search_kwargs
        )

        return retriever

    def ask_question(
        self,
        question: str,
        user_id: int,
        document_id: Optional[int] = None,
        chat_history: Optional[List[dict]] = None,
        query_mode: str = "normal"
    ) -> dict:
        """
        Answer a question using RAG.

        Args:
            question: User's question
            user_id: For retrieving correct documents
            document_id: Optional - limit to specific document
            chat_history: Previous messages for context
            query_mode: "normal", "eli5" (explain like I'm 5),
                       "practice" (generate practice problems)

        Returns:
            dict with answer and source documents

        Senior Tip: The magic happens in the retriever - it finds
        the most relevant chunks using semantic similarity, not
        just keyword matching!
        """
        # Modify question based on query mode
        if query_mode == "eli5":
            question = f"Explain this like I'm 5 years old: {question}"
        elif query_mode == "practice":
            question = f"Give me 5 practice problems about: {question}"
        elif query_mode == "summary":
            question = f"Give me a concise summary of: {question}"

        # Get retriever
        retriever = self.get_retriever(user_id, document_id)

       
        lc_chat_history = []
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    lc_chat_history.append(
                        HumanMessage(content=msg["content"])
                    )
                elif msg["role"] == "assistant":
                    lc_chat_history.append(
                        AIMessage(content=msg["content"])
                    )

        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            return_source_documents=True,
            combine_docs_chain_kwargs={
                "prompt": STUDY_QA_PROMPT
            }
        )

        # Execute chain
        result = chain.invoke({
            "question": question,
            "chat_history": lc_chat_history
        })

      
        sources = []
        for doc in result.get("source_documents", []):
            sources.append({
                "content": doc.page_content[:200] + "...",
                "page": doc.metadata.get("page", "unknown"),
                "document_id": doc.metadata.get("document_id")
            })

        return {
            "answer": result["answer"],
            "sources": sources,
            "query_mode": query_mode
        }

    def generate_flashcards(
        self,
        user_id: int,
        document_id: int,
        topic: Optional[str] = None,
        num_cards: int = 10,
        difficulty: str = "medium"
    ) -> List[dict]:
   
        import json
        retriever = self.get_retriever(
            user_id,
            document_id,
            k=5
        )

      
        search_query = topic if topic else "main concepts and key information"

        # Get relevant chunks
        relevant_docs = retriever.invoke(search_query)

     
        context = "\n\n---\n\n".join([
            doc.page_content for doc in relevant_docs
        ])

        if not context:
            raise ValueError(
                "No content found in document. "
                "Make sure the PDF was processed successfully."
            )

        # Generate flashcards using Claude
        prompt = FLASHCARD_PROMPT.format(
            context=context,
            num_cards=num_cards,
            topic=topic or "all key concepts",
            difficulty=difficulty
        )

        response = self.flashcard_llm.invoke([
            HumanMessage(content=prompt)
        ])

        # Parse JSON response
        try:
            # Clean response (remove markdown code blocks if present)
            response_text = response.content
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            flashcards = json.loads(response_text.strip())

            # Validate structure
            validated = []
            for card in flashcards:
                if "question" in card and "answer" in card:
                    validated.append({
                        "question": card["question"],
                        "answer": card["answer"],
                        "difficulty": card.get("difficulty", difficulty)
                    })

            return validated

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse flashcards from AI response: {e}")

    def search_documents(
        self,
        query: str,
        user_id: int,
        document_id: Optional[int] = None,
        k: int = 5
    ) -> List[dict]:
    
        retriever = self.get_retriever(user_id, document_id, k=k)

        results = retriever.invoke(query)

        return [
            {
                "content": doc.page_content,
                "page": doc.metadata.get("page", "unknown"),
                "document_id": doc.metadata.get("document_id"),
                "relevance_score": doc.metadata.get("score", None)
            }
            for doc in results
        ]             