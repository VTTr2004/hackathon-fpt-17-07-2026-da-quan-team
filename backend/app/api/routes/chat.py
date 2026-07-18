from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.chat_message import ChatMessage
from app.models.document import Document
from app.models.startup import Startup
from app.schemas.chat import ChatMessageRead, ChatRequest, ChatResponse
from app.services.chat_service import _normalize_citations, answer_question

router = APIRouter()


def startup_profile(startup: Startup) -> dict:
    """Profile fields fed into the RAG index so chat can answer about the startup itself."""
    return {
        "name": startup.name,
        "industry": startup.industry,
        "stage": startup.stage,
        "primary_location": startup.primary_location,
        "facts": startup.facts or {},
    }


@router.get("/{startup_id}/chat/history", response_model=list[ChatMessageRead])
async def chat_history(startup_id: UUID, db: AsyncSession = Depends(get_db)) -> list[ChatMessageRead]:
    if await db.get(Startup, startup_id) is None:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
    messages = await db.scalars(
        select(ChatMessage)
        .where(ChatMessage.startup_id == startup_id)
        .order_by(ChatMessage.created_at)
    )
    # Normalize legacy citation markers (【SOURCE n】, [SOURCE n], 【n】) saved before the fix to [n].
    return [
        ChatMessageRead(
            role=message.role,
            content=_normalize_citations(message.content) if message.role == "assistant" else message.content,
            citations=message.citations or [],
            created_at=message.created_at,
        )
        for message in messages
    ]


@router.post("/{startup_id}/chat", response_model=ChatResponse)
async def chat_with_documents(
    startup_id: UUID, payload: ChatRequest, db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    startup = await db.get(Startup, startup_id)
    if startup is None:
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
        startup_profile(startup),
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
