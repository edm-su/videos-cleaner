import os

import pytest
from httpx import AsyncClient

from videos_cleaner.adapters.repositories.meta_repository import (
    YoutubeDataApiRepository,
)

pytestmark = pytest.mark.anyio


class TestYouTubeDataAPIRepostiory:
    @pytest.fixture
    async def repo(self, http_client: AsyncClient) -> YoutubeDataApiRepository:
        if (key := os.getenv("YOUTUBE_DATA_API_KEY")) is None:
            raise AssertionError(
                "Переменная окружения YOUTUBE_DATA_API_KEY не установлена"
            )
        return YoutubeDataApiRepository(key, http_client)

    @pytest.mark.parametrize(
        ("yt_id", "expect"), [("l44WHWxXuiw", False), ("nhMIpxZe1R8", True)]
    )
    async def test_embeddable(
        self, repo: YoutubeDataApiRepository, yt_id: str, expect: bool
    ) -> None:
        result = await repo.is_embeddable(yt_id)

        assert result is expect
