# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StudyAI is an AI-powered study assistant. Users upload PDFs and the app uses RAG to answer questions, generate flashcards, and support spaced-repetition learning.

## Development Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Architecture, monorepo, CI/CD | Partial |
| 2 | FastAPI backend, auth, CRUD, Alembic | **Done** |
| 3 | PDF processing, chunking, Pinecone embeddings | **Done** |
| 4 | Claude RAG, flashcard generation, prompt engineering | **Done** |
| 5 | SM-2 spaced repetition, review scheduling, analytics | **Done** |
| 6 | Next.js + TypeScript frontend (upload, chat, flashcards, dashboard) | **Done** |
| 7 | WebSocket real-time chat, performance, security | **Done** |
| 8 | Docker, Render + Vercel deployment, GitHub Actions CI/CD | **Done** |

## Deployed URLs

- **Frontend**: https://study-ai-sepia.vercel.app
- **Backend**: https://studyai-vx3y.onrender.com
- **API Docs**: https://studyai-vx3y.onrender.com/docs

## Running the Project

```bash
# Backend
cd backend
alembic upgrade head        # apply DB migrations first
uvicorn app.main:app --reload

# Frontend (once scaffolded)
cd frontend
npm run dev
```

Backend API docs: `http://localhost:8000/docs`
Frontend: `http://localhost:3000`

## Key Environment Variables (`.env` in `backend/`)

```
DATABASE_URL=
SECRET_KEY=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=studyai
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

## Architecture

```
backend/
  app/
    main.py          # FastAPI app, CORS, router registration, startup hooks
    config.py        # Pydantic settings (loaded from .env)
    database.py      # SQLAlchemy engine, SessionLocal, Base, init_db()
    api/             # Route handlers (auth, documents, chat, flashcards, analytics)
    models/          # SQLAlchemy ORM models (user, document, document_chunk, flashcard, study_session)
    schemas/         # Pydantic request/response schemas
    services/        # Business logic
    utils/
  uploads/           # Uploaded PDFs stored here
```

### Service Layer

- **`rag_services.py` (`RAGService`)** — Core RAG logic. Uses `ChatAnthropic` (claude-3-haiku for Q&A, claude-3-sonnet for flashcards) + `OpenAIEmbeddings` (text-embedding-3-small). Retrieves chunks from Pinecone, runs `ConversationalRetrievalChain`, and generates flashcards via a structured JSON prompt.
- **`langchain_pdf_service.py` (`LangChainPDFService`)** — Loads PDFs with `PyPDFLoader`, splits into 1000-char chunks (200 overlap) via `RecursiveCharacterTextSplitter`, and stores embeddings in Pinecone.
- **`pinecone_service.py` (`PineconeService`)** — Wraps Pinecone vector store access; vectors are namespaced per user.
- **`auth_service.py`** — JWT auth (HS256, 7-day tokens via `python-jose` + `passlib`).
- **`document_service.py`** — Handles PDF file storage and DB record management.

### Data Flow: PDF Upload → Q&A

1. User uploads PDF → saved to `uploads/` → `document_service` creates DB record
2. `LangChainPDFService` loads + chunks PDF → embeddings generated via OpenAI → stored in Pinecone with `{document_id, user_id}` metadata
3. On chat query → `RAGService` retrieves top-k similar chunks from Pinecone (filtered by `user_id`/`document_id`) → feeds context + chat history into Claude via `ConversationalRetrievalChain`

### API Routes (all prefixed `/api/v1`)

| Router | File |
|--------|------|
| `/auth` | `api/auth.py` |
| `/documents` | `api/documents.py` |
| `/chat` | `api/chat.py` |
| `/flashcards` | `api/flashcards.py` |

### Database

PostgreSQL via SQLAlchemy. Migrations are managed with Alembic — run `alembic upgrade head` before starting the server.

```bash
cd backend
alembic revision --autogenerate -m "describe change"  # generate migration from model changes
alembic upgrade head                                   # apply all pending migrations
alembic downgrade -1                                   # roll back one migration
alembic history                                        # view migration history
alembic current                                        # show current DB revision
```

Migration files live in `backend/alembic/versions/`. The `env.py` pulls `DATABASE_URL` from `.env` automatically and imports all models for autogenerate support.

### AI Models Used

- **Q&A**: `claude-3-haiku-20240307` (fast, low cost)
- **Flashcard generation**: `claude-3-sonnet-20240229` (higher quality)
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Vector DB**: Pinecone (index: `studyai`)

> Note: `langchain_pdf_service.py` has leftover ChromaDB references that are unused — the active vector store is Pinecone via `pinecone_service.py`.
