from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.chat_message import ChatMessage
from app.models.document import Document
from app.models.startup import Startup
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import answer_question

router = APIRouter()


@router.post("/{startup_id}/chat", response_model=ChatResponse)
async def chat_with_documents(
    startup_id: UUID, payload: ChatRequest, db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    if await db.get(Startup, startup_id) is None:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
    docs = list(await db.scalars(select(Document).where(Document.startup_id == startup_id)))
    response = await answer_question(
        payload.question,
        [{"id": str(doc.id), "filename": doc.filename, "text": doc.extracted_text} for doc in docs],
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
