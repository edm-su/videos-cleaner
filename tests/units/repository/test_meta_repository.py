from collections.abc import AsyncGenerator
from typing import Literal

import pytest
import respx
from httpx import AsyncClient, Response

from videos_cleaner.adapters.repositories.meta_repository import (
    MetaRepostiory,
    YoutubeDataApiRepository,
)
from videos_cleaner.domain.interfaces.meta_repository import ExistsStatus

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient() as client:
        yield client


class TestMetaRepository:
    @pytest.fixture
    def repo(self, client: AsyncClient) -> MetaRepostiory:
        return MetaRepostiory(client)

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


class TestYouTubeDataAPIRepository:
    @pytest.fixture
    def repo(self, client: AsyncClient) -> YoutubeDataApiRepository:
        return YoutubeDataApiRepository("secret", client)

    @respx.mock
    @pytest.mark.parametrize(
        ("items", "expected"), [([{"status": {"embeddable": True}}], True), ([], False)]
    )
    async def test_is_embeddable(
        self,
        repo: YoutubeDataApiRepository,
        items: list[dict[Literal["Embeddable"], bool]],
        expected: bool,
    ) -> None:
        route = respx.get(
            "https://youtube.googleapis.com/youtube/v3/videos?part=status&id=test&fields=items(status/embeddable)&key=secret"
        )
        route.return_value = Response(200, json={"items": items})

        result = await repo.is_embeddable("test")

        assert route.called
        assert expected is result
