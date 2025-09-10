from typing import final, override

from httpx import AsyncClient
from wireup import service

from videos_cleaner.domain.interfaces.meta_repository import (
    ExistsStatus,
    IMetaRepository,
    MetaRepositoryError,
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
            case code:
                raise MetaRepositoryError(response.text, code)
