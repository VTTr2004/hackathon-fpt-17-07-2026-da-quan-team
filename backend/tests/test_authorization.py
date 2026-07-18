from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.auth import get_owned_startup


@pytest.mark.asyncio
async def test_startup_owner_can_edit_draft() -> None:
    user = SimpleNamespace(id=uuid4(), role="startup")
    startup = SimpleNamespace(id=uuid4(), owner_id=user.id, status="draft")
    db = SimpleNamespace(get=AsyncMock(return_value=startup))
    assert await get_owned_startup(startup.id, user, db, require_draft=True) is startup


@pytest.mark.asyncio
async def test_investor_cannot_edit_startup() -> None:
    user = SimpleNamespace(id=uuid4(), role="investor")
    startup = SimpleNamespace(id=uuid4(), owner_id=uuid4(), status="draft")
    db = SimpleNamespace(get=AsyncMock(return_value=startup))
    with pytest.raises(HTTPException) as error:
        await get_owned_startup(startup.id, user, db, require_draft=True)
    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_locked_submission_cannot_be_edited() -> None:
    user = SimpleNamespace(id=uuid4(), role="startup")
    startup = SimpleNamespace(id=uuid4(), owner_id=user.id, status="submitted")
    db = SimpleNamespace(get=AsyncMock(return_value=startup))
    with pytest.raises(HTTPException) as error:
        await get_owned_startup(startup.id, user, db, require_draft=True)
    assert error.value.status_code == 409
