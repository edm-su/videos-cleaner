from collections.abc import AsyncGenerator

import pytest
import respx
from httpx import AsyncClient, Response

from videos_cleaner.adapters.repositories.video_repository import VideoRepository
from videos_cleaner.domain.interfaces.video_repository import (
    VideoIsAlreadyDeletedError,
    VideoIsNotDeletedError,
    VideoNotFoundError,
    VideoRepostiryError,
)

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient() as client:
        yield client


@pytest.fixture
def repo(client: AsyncClient) -> VideoRepository:
    return VideoRepository(client, "http://test")


class TestVideoRepository:
    @respx.mock
    async def test_restore(self, repo: VideoRepository) -> None:
        route = respx.post("http://test/videos/test/restore")

        await repo.restore("test")

        assert route.called

    @respx.mock
    async def test_get_all(self, repo: VideoRepository) -> None:
        route = respx.get("http://test/videos?include_deleted=true&skip=0&limit=50")
        route.return_value = Response(
            200,
            json=[
                {
                    "id": 1,
                    "title": "Active Video",
                    "slug": "active-video",
                    "deleted": False,
                    "date": "2024-01-01",
                    "yt_id": "abc123",
                    "yt_thumbnail": "https://example.com/thumb.jpg",
                    "duration": 180,
                    "is_favorite": False,
                    "is_blocked_in_russia": False,
                }
            ],
            headers={"x-total-count": "1"},
        )

        videos = await repo.get_all()

        assert route.called
        assert videos.total_count == 1
        assert videos.videos[0].slug == "active-video"

    @respx.mock
    async def test_delete(self, repo: VideoRepository) -> None:
        route = respx.delete("http://test/videos/test")
        route.return_value = Response(204)

        await repo.delete("test")

        assert route.called

    @respx.mock
    async def test_hard_delete(self, repo: VideoRepository) -> None:
        route = respx.delete("http://test/videos/test?temporary=false")
        route.return_value = Response(204)

        await repo.delete("test", temporary=False)

        assert route.called


class TestNegativeVideoRepository:
    @respx.mock
    async def test_restore_not_exists_video(self, repo: VideoRepository) -> None:
        route = respx.post("http://test/videos/test/restore")
        route.return_value = Response(404)

        with pytest.raises(VideoNotFoundError):
            await repo.restore("test")

        assert route.called

    @respx.mock
    async def test_restore_not_deleted_video(self, repo: VideoRepository) -> None:
        route = respx.post("http://test/videos/test/restore")
        route.return_value = Response(409)

        with pytest.raises(VideoIsNotDeletedError):
            await repo.restore("test")

        assert route.called

    @respx.mock
    async def test_get_all_service_error(self, repo: VideoRepository) -> None:
        route = respx.get("http://test/videos")
        route.return_value = Response(500)

        with pytest.raises(VideoRepostiryError):
            _ = await repo.get_all()

        assert route.called

    @respx.mock
    async def test_delete_not_exists_video(self, repo: VideoRepository) -> None:
        route = respx.delete("http://test/videos/test")
        route.return_value = Response(404)

        with pytest.raises(VideoNotFoundError):
            await repo.delete("test")

        assert route.called

    @respx.mock
    async def test_delete_alreade_deleted_video(self, repo: VideoRepository) -> None:
        route = respx.delete("http://test/videos/test")
        route.return_value = Response(409)

        with pytest.raises(VideoIsAlreadyDeletedError):
            await repo.delete("test")

        assert route.called
