from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.startup import Startup
from app.schemas.startup import StartupCreate, StartupRead, StartupUpdate

router = APIRouter()


async def _get_startup_or_404(startup_id: UUID, db: AsyncSession) -> Startup:
    startup = await db.get(Startup, startup_id)
    if startup is None:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
    return startup


@router.get("", response_model=list[StartupRead])
async def list_startups(db: AsyncSession = Depends(get_db)) -> list[Startup]:
    result = await db.scalars(select(Startup).order_by(Startup.created_at.desc()))
    return list(result)


@router.post("", response_model=StartupRead, status_code=status.HTTP_201_CREATED)
async def create_startup(payload: StartupCreate, db: AsyncSession = Depends(get_db)) -> Startup:
    startup = Startup(**payload.model_dump())
    db.add(startup)
    await db.commit()
    await db.refresh(startup)
    return startup


@router.get("/{startup_id}", response_model=StartupRead)
async def get_startup(startup_id: UUID, db: AsyncSession = Depends(get_db)) -> Startup:
    return await _get_startup_or_404(startup_id, db)


@router.patch("/{startup_id}", response_model=StartupRead)
async def update_startup(startup_id: UUID, payload: StartupUpdate, db: AsyncSession = Depends(get_db)) -> Startup:
    startup = await _get_startup_or_404(startup_id, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(startup, key, value)
    await db.commit()
    await db.refresh(startup)
    return startup
