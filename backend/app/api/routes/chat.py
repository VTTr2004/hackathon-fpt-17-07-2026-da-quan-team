from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_accessible_startup, get_current_user
from app.db.session import get_db
from app.models.chat_message import ChatMessage
from app.models.document import Document
from app.models.startup_version import StartupVersion
from app.models.user import User
from app.schemas.chat import ChatMessageRead, ChatRequest, ChatResponse
from app.services.chat_service import answer_question

router = APIRouter()


async def _chat_scope(
    startup_id: UUID, user: User, db: AsyncSession
) -> tuple[list[Document], StartupVersion | None]:
    await get_accessible_startup(startup_id, user, db)
    if user.role == "startup":
        documents = list(await db.scalars(select(Document).where(Document.startup_id == startup_id)))
        return documents, None

    version = await db.scalar(
        select(StartupVersion)
        .where(StartupVersion.startup_id == startup_id)
        .order_by(StartupVersion.version_number.desc())
        .limit(1)
    )
    if version is None:
        raise HTTPException(status_code=409, detail="Hồ sơ chưa được nộp")
    document_ids = [UUID(item) for item in version.document_ids]
    documents = list(
        await db.scalars(
            select(Document).where(Document.id.in_(document_ids), Document.visibility == "shared")
        )
    )
    return documents, version


@router.get("/{startup_id}/chat/history", response_model=list[ChatMessageRead])
async def chat_history(
    startup_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ChatMessage]:
    _, version = await _chat_scope(startup_id, user, db)
    query = select(ChatMessage).where(ChatMessage.startup_id == startup_id, ChatMessage.user_id == user.id)
    if version is not None:
        query = query.where(ChatMessage.startup_version_id == version.id)
    else:
        query = query.where(ChatMessage.startup_version_id.is_(None))
    return list(await db.scalars(query.order_by(ChatMessage.created_at)))


@router.post("/{startup_id}/chat", response_model=ChatResponse)
async def chat_with_documents(
    startup_id: UUID,
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    docs, version = await _chat_scope(startup_id, user, db)
    query = (
        select(ChatMessage)
        .where(ChatMessage.startup_id == startup_id, ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(8)
    )
    if version is not None:
        query = query.where(ChatMessage.startup_version_id == version.id)
    else:
        query = query.where(ChatMessage.startup_version_id.is_(None))
    prior = list(await db.scalars(query))
    history = [{"role": message.role, "content": message.content} for message in reversed(prior)]
    response = await answer_question(
        f"{startup_id}:{version.id if version else 'draft'}:{user.id}",
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
            ChatMessage(
                startup_id=startup_id,
                startup_version_id=version.id if version else None,
                user_id=user.id,
                role="user",
                content=payload.question,
            ),
            ChatMessage(
                startup_id=startup_id,
                startup_version_id=version.id if version else None,
                user_id=user.id,
                role="assistant",
                content=response.answer,
                citations=[citation.model_dump(mode="json") for citation in response.citations],
            ),
        ]
    )
    await db.commit()
    return response
