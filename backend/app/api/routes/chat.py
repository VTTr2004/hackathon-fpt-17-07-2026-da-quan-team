from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.chat_message import ChatMessage
from app.models.document import Document
from app.models.startup import Startup
from app.schemas.chat import ChatMessageRead, ChatRequest, ChatResponse
from app.services.chat_service import answer_question

router = APIRouter()


@router.get("/{startup_id}/chat/history", response_model=list[ChatMessageRead])
async def chat_history(startup_id: UUID, db: AsyncSession = Depends(get_db)) -> list[ChatMessage]:
    if await db.get(Startup, startup_id) is None:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
    return list(
        await db.scalars(
            select(ChatMessage)
            .where(ChatMessage.startup_id == startup_id)
            .order_by(ChatMessage.created_at)
        )
    )


@router.post("/{startup_id}/chat", response_model=ChatResponse)
async def chat_with_documents(
    startup_id: UUID, payload: ChatRequest, db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    if await db.get(Startup, startup_id) is None:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
    docs = list(await db.scalars(select(Document).where(Document.startup_id == startup_id)))
    prior = list(
        await db.scalars(
            select(ChatMessage)
            .where(ChatMessage.startup_id == startup_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(8)
        )
    )
    history = [{"role": message.role, "content": message.content} for message in reversed(prior)]
    response = await answer_question(
        str(startup_id),
        [
            {
                "id": str(doc.id),
                "filename": doc.filename,
                "text": doc.extracted_text,
                "storage_path": doc.storage_path,
            }
            for doc in docs
        ],
        payload.question,
        history,
    )
    db.add_all(
        [
            ChatMessage(startup_id=startup_id, role="user", content=payload.question),
            ChatMessage(
                startup_id=startup_id,
                role="assistant",
                content=response.answer,
                citations=[citation.model_dump(mode="json") for citation in response.citations],
            ),
        ]
    )
    await db.commit()
    return response
