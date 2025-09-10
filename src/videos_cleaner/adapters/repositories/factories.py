from collections.abc import AsyncIterator

from httpx import AsyncClient
from wireup import service


@service
async def make_http_client() -> AsyncIterator[AsyncClient]:
    """Создаёт http клиент."""
    async with AsyncClient() as client:
        yield client
