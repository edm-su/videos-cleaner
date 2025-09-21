from typing import Literal, final, override

from httpx import AsyncClient
from wireup import service

from videos_cleaner.domain.interfaces.meta_repository import (
    ExistsStatus,
    IMetaRepository,
    MetaRepositoryError,
    UnauthorizedError,
)


@final
@service
class MetaRepostiory(IMetaRepository):
    """Репозиторий информации о youtube видео с помощью OEmbed api youtube."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    @override
    async def is_exists(self, yt_id: str) -> ExistsStatus:
        response = await self._client.head(
            f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={yt_id}"
        )

        match response.status_code:
            case 200:
                return ExistsStatus.EXISTS
            case 404:
                return ExistsStatus.REMOVED
            case 403:
                return ExistsStatus.HIDDEN
            case 401:
                raise UnauthorizedError
            case code:
                raise MetaRepositoryError(response.text, code)

    @override
    async def is_embeddable(self, yt_id: str) -> bool:
        return await super().is_embeddable(yt_id)


@final
class YoutubeDataApiRepository(IMetaRepository):
    """Репозиторий информации о youtube видео с помощью YouTube Data API."""

    def __init__(self, key: str, client: AsyncClient) -> None:
        self._key = key
        self._client = client
        super().__init__()

    @override
    async def is_exists(self, yt_id: str) -> ExistsStatus:
        return await super().is_exists(yt_id)

    @override
    async def is_embeddable(self, yt_id: str) -> bool:
        response = await self._client.get(
            f"https://youtube.googleapis.com/youtube/v3/videos?part=status&id={yt_id}&fields=items(status/embeddable)&key={self._key}"
        )

        match response.status_code:
            case 200:
                data: dict[
                    Literal["items"],
                    list[dict[Literal["status"], dict[Literal["embeddable"], bool]]],
                ] = response.json()
                if item := data["items"]:
                    return item[0]["status"]["embeddable"]
                return False
            case 403:
                raise UnauthorizedError
            case code:
                raise MetaRepositoryError(response.text, code)
