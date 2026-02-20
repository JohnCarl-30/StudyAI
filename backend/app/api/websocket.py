"""
WebSocket endpoint for real-time streaming chat.

Flow:
  1. Client connects: ws://host/api/v1/ws/chat?token=<jwt>
  2. Client sends JSON: {"question": "...", "document_id": 1, "query_mode": "normal"}
  3. Server streams back text chunks as plain strings
  4. Server sends JSON {"type": "done", "sources": [...]} when complete
"""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.utils.security import decode_access_token
from app.models.user import User
from app.services.rag_services import RAGService
from app.api.deps import get_rag_service

router = APIRouter()
_rag: RAGService | None = None


def _get_rag() -> RAGService:
    global _rag
    if _rag is None:
        _rag = get_rag_service()
    return _rag


def _authenticate(token: str, db: Session) -> User | None:
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(...),
):
    db: Session = SessionLocal()
    try:
        user = _authenticate(token, db)
        if not user:
            await websocket.accept()
            await websocket.close(code=4001, reason="Unauthorized")
            return

        await websocket.accept()

        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            question = data.get("question", "").strip()
            if not question:
                continue

            document_id = data.get("document_id")
            query_mode = data.get("query_mode", "normal")
            chat_history = data.get("chat_history", [])

            try:
                # RAGService.ask_question is synchronous; run it and stream the answer
                # word-by-word to simulate streaming (true streaming requires LangChain streaming callbacks)
                rag = _get_rag()
                result = rag.ask_question(
                    question=question,
                    user_id=user.id,
                    document_id=document_id,
                    chat_history=chat_history,
                    query_mode=query_mode,
                )

                answer: str = result["answer"]
                # Stream word-by-word
                words = answer.split(" ")
                for i, word in enumerate(words):
                    chunk = word if i == len(words) - 1 else word + " "
                    await websocket.send_text(json.dumps({"type": "chunk", "text": chunk}))

                # Send completion message with sources
                await websocket.send_text(json.dumps({
                    "type": "done",
                    "sources": result.get("sources", []),
                    "query_mode": result.get("query_mode"),
                }))

            except Exception as e:
                await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))

    finally:
        db.close()
