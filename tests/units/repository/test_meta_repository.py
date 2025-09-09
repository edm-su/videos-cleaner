from collections.abc import AsyncGenerator

import pytest
import respx
from httpx import AsyncClient, Response

from videos_cleaner.adapters.repositories.meta_repository import MetaRepostiory
from videos_cleaner.domain.interfaces.meta_repository import ExistsStatus

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient() as client:
        yield client


@pytest.fixture
def repo(client: AsyncClient) -> MetaRepostiory:
    return MetaRepostiory(client)


class TestMetaRepository:
    @respx.mock
    async def test_exists(self, repo: MetaRepostiory) -> None:
        route = respx.head(
            "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=test"
        )
        route.return_value = Response(200)

        result = await repo.is_exists("test")

        assert route.called
        assert result == ExistsStatus.EXISTS

    @respx.mock
    async def test_hidden(self, repo: MetaRepostiory) -> None:
        route = respx.head(
            "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=test"
        )
        route.return_value = Response(403)

        result = await repo.is_exists("test")

        assert route.called
        assert result == ExistsStatus.HIDDEN

    @respx.mock
    async def test_removed(self, repo: MetaRepostiory) -> None:
        route = respx.head(
            "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=test"
        )
        route.return_value = Response(404)

        result = await repo.is_exists("test")

        assert route.called
        assert result == ExistsStatus.REMOVED
