from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient


@pytest.fixture
async def http_client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient() as client:
        yield client
