from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes.startups import request_access
from app.schemas.investor import AccessRequestCreate


@pytest.mark.asyncio
async def test_investor_cannot_request_data_room_for_incomplete_startup() -> None:
    investor = SimpleNamespace(id=uuid4(), role="investor", full_name="Investor", email="investor@example.com")
    startup = SimpleNamespace(
        id=uuid4(),
        status="submitted",
        discoverable=True,
        current_version=1,
        name="Incomplete Startup",
        industry=None,
        stage=None,
        primary_location=None,
        facts={},
    )
    db = SimpleNamespace(
        get=AsyncMock(return_value=startup),
        scalar=AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as error:
        await request_access(startup.id, AccessRequestCreate(), investor, db)

    assert error.value.status_code == 409
    assert "chưa đủ điều kiện" in error.value.detail
