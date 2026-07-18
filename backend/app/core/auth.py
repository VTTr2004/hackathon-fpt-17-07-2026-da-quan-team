from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.startup import Startup
from app.models.startup_access import StartupAccess
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = decode_access_token(credentials.credentials) if credentials else None
    user = await db.get(User, user_id) if user_id else None
    if user is None or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đăng nhập không hợp lệ")
    return user


def require_role(*roles: str) -> Callable:
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền thực hiện thao tác này"
            )
        return user

    return dependency


async def can_investor_access(startup_id: UUID, investor_id: UUID, db: AsyncSession) -> bool:
    access_id = await db.scalar(
        select(StartupAccess.id).where(
            StartupAccess.startup_id == startup_id,
            StartupAccess.investor_id == investor_id,
            StartupAccess.status == "active",
        )
    )
    return access_id is not None


async def get_accessible_startup(startup_id: UUID, user: User, db: AsyncSession) -> Startup:
    startup = await db.get(Startup, startup_id)
    if startup is None:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
    if user.role == "startup" and startup.owner_id == user.id:
        return startup
    if user.role == "investor" and await can_investor_access(startup_id, user.id, db):
        return startup
    raise HTTPException(status_code=404, detail="Startup không tồn tại")


async def get_owned_startup(startup_id: UUID, user: User, db: AsyncSession, *, require_draft: bool = False) -> Startup:
    startup = await db.get(Startup, startup_id)
    if startup is None or user.role != "startup" or startup.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
    if require_draft and startup.status != "draft":
        raise HTTPException(status_code=409, detail="Phiên bản đã nộp đang bị khóa. Hãy tạo bản nháp mới để cập nhật.")
    return startup
