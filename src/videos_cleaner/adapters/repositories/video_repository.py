from json import JSONDecodeError
from typing import Annotated, final, override

from httpx import AsyncClient, Response
from pydantic import TypeAdapter
from wireup import Inject, service

from videos_cleaner.domain.interfaces.video_repository import (
    IVideoRepository,
    VideoIsAlreadyDeletedError,
    VideoIsNotDeletedError,
    VideoNotFoundError,
    VideoRepostiryError,
)
from videos_cleaner.entities.video import Video, VideoList


@final
@service
class VideoRepository(IVideoRepository):
    """Репозиторий видео API edm.su."""

    def __init__(
        self,
        client: AsyncClient,
        base_url: Annotated[str, Inject(param="video_url")] = "http://localhost",
    ) -> None:
        self._client = client
        self.base_url = base_url
        super().__init__()

    @override
    async def get_all(self, offset: int = 0, *, limit: int = 50) -> VideoList:
        response = await self._client.get(
            f"{self.base_url}/videos",
            params={"include_deleted": True, "skip": offset, "limit": limit},
        )
        match response.status_code:
            case 200:
                adapter = TypeAdapter(list[Video])

                videos = adapter.validate_json(response.text)
                x_total: str = response.headers.get("x-total-count", "0")  # pyright: ignore[reportAny]
                count = int(x_total)

                return VideoList(total_count=count, videos=videos)
            case _:
                self._raise_unknown_error(response)
                return VideoList(total_count=0, videos=[])

    @override
    async def restore(self, slug: str) -> None:
        response = await self._client.post(f"{self.base_url}/videos/{slug}/restore")
        match response.status_code:
            case 200:
                return
            case 409:
                raise VideoIsNotDeletedError
            case 404:
                raise VideoNotFoundError
            case _:
                self._raise_unknown_error(response)

    def _raise_unknown_error(self, response: Response) -> None:
        try:
            body: dict[str, str] = response.json()  # pyright: ignore[reportAny]
            message = body.get("detail", "Незивестная ошибка")
        except JSONDecodeError:
            message = "Неизвестная ошибка"
        raise VideoRepostiryError(message, response.status_code)

    @override
    async def delete(self, slug: str, *, temporary: bool = True) -> None:
        response = await self._client.delete(
            f"{self.base_url}/videos/{slug}",
            params={"temporary": temporary},
        )

        match response.status_code:
            case 204:
                return
            case 404:
                raise VideoNotFoundError
            case 409:
                raise VideoIsAlreadyDeletedError
            case _:
                self._raise_unknown_error(response)
