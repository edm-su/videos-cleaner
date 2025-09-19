import pytest
from pytest_mock import MockFixture

from videos_cleaner.domain.interfaces.meta_repository import (
    ExistsStatus,
    IMetaRepository,
    MetaRepositoryError,
    UnauthorizedError,
)
from videos_cleaner.domain.interfaces.video_repository import (
    IVideoRepository,
    VideoIsAlreadyDeletedError,
    VideoIsNotDeletedError,
)
from videos_cleaner.domain.use_cases.video_use_case import VideoCleanerUseCase
from videos_cleaner.entities.video import Video, VideoList

pytestmark = pytest.mark.anyio


@pytest.fixture
def video_repository(mocker: MockFixture) -> IVideoRepository:
    return mocker.AsyncMock(IVideoRepository)


@pytest.fixture
def meta_repository(mocker: MockFixture) -> IMetaRepository:
    return mocker.AsyncMock(IMetaRepository)


@pytest.fixture
def youtube_data_api_repository(mocker: MockFixture) -> IMetaRepository:
    return mocker.AsyncMock(IMetaRepository)


@pytest.fixture
def use_case(
    video_repository: IVideoRepository,
    meta_repository: IMetaRepository,
    youtube_data_api_repository: IMetaRepository,
) -> VideoCleanerUseCase:
    return VideoCleanerUseCase(
        video_repository, meta_repository, youtube_data_api_repository
    )


class TestCleanerUseCase:
    async def test_video_cleaner(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=1, videos=[Video(deleted=False, slug="test", yt_id="test")]
            ),
        )
        mock_delete = mocker.spy(use_case._video_repo, "delete")  # pyright: ignore[reportPrivateUsage]
        mock_restore = mocker.spy(use_case._video_repo, "restore")  # pyright: ignore[reportPrivateUsage]
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            return_value=ExistsStatus.EXISTS,
        )

        stats = await use_case.execute()

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        _ = mock_delete.assert_not_awaited()
        _ = mock_restore.assert_not_awaited()
        assert stats.unchanged == 1

    async def test_restore_video(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=1, videos=[Video(deleted=True, slug="test", yt_id="test")]
            ),
        )
        mock_delete = mocker.spy(use_case._video_repo, "delete")  # pyright: ignore[reportPrivateUsage]
        mock_restore = mocker.spy(use_case._video_repo, "restore")  # pyright: ignore[reportPrivateUsage]
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            return_value=ExistsStatus.EXISTS,
        )

        stats = await use_case.execute()

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        _ = mock_delete.assert_not_awaited()
        _ = mock_restore.assert_awaited()
        assert stats.restored == 1

    async def test_permanently_delete_temporary_deleted_video(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        """
        Удалить видео навсегда, которое было временно удалено ранее
        """
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=1, videos=[Video(deleted=True, slug="test", yt_id="test")]
            ),
        )
        mock_delete = mocker.spy(use_case._video_repo, "delete")  # pyright: ignore[reportPrivateUsage]
        mock_restore = mocker.spy(use_case._video_repo, "restore")  # pyright: ignore[reportPrivateUsage]
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            return_value=ExistsStatus.REMOVED,
        )

        stats = await use_case.execute()

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        _ = mock_delete.assert_awaited_once_with("test", temporary=False)
        _ = mock_restore.assert_not_awaited()
        assert stats.deleted == 1

    @pytest.mark.parametrize(
        ("status", "temporary", "name"),
        [
            (ExistsStatus.HIDDEN, True, "hidden"),
            (ExistsStatus.REMOVED, False, "deleted"),
        ],
    )
    async def test_delete_video(
        self,
        use_case: VideoCleanerUseCase,
        mocker: MockFixture,
        status: ExistsStatus,
        temporary: bool,
        name: str,
    ) -> None:
        """
        Удалить видео
        """
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=1, videos=[Video(deleted=False, slug="test", yt_id="test")]
            ),
        )
        mock_delete = mocker.spy(use_case._video_repo, "delete")  # pyright: ignore[reportPrivateUsage]
        mock_restore = mocker.spy(use_case._video_repo, "restore")  # pyright: ignore[reportPrivateUsage]
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            return_value=status,
        )

        stats = await use_case.execute()

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        _ = mock_delete.assert_awaited_once_with("test", temporary=temporary)
        _ = mock_restore.assert_not_awaited()
        assert getattr(stats, name) == 1

    async def test_multiple_pages(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        use_case.batch_size = 1
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=2, videos=[Video(deleted=False, slug="test", yt_id="test")]
            ),
        )
        _ = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            return_value=ExistsStatus.EXISTS,
        )

        stats = await use_case.execute()

        assert mock_get_all.await_count == 2
        assert stats.total == 2

    async def test_limit(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=2,
                videos=[
                    Video(deleted=False, slug="test", yt_id="test") for _ in range(2)
                ],
            ),
        )
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            return_value=ExistsStatus.EXISTS,
        )

        stats = await use_case.execute(1)

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        assert stats.total == 1

    async def test_limit_is_very_biggest_then_total(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        """Лимит очень большой по отношению к общему количеству элементов."""
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=1,
                videos=[Video(deleted=False, slug="test", yt_id="test")],
            ),
        )
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            return_value=ExistsStatus.EXISTS,
        )

        stats = await use_case.execute(100_000)

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        assert stats.total == 1


class TestUseCaseErrors:
    async def test_delete_error(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=1,
                videos=[Video(deleted=False, slug="test", yt_id="test")],
            ),
        )
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            return_value=ExistsStatus.REMOVED,
        )
        mock_delete = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "delete",
            side_effect=VideoIsAlreadyDeletedError,
        )

        result = await use_case.execute()

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        _ = mock_delete.assert_awaited_once()
        assert result.unchanged == 1

    async def test_restore_error(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=1,
                videos=[Video(deleted=True, slug="test", yt_id="test")],
            ),
        )
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            return_value=ExistsStatus.EXISTS,
        )
        mock_restore = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "restore",
            side_effect=VideoIsNotDeletedError,
        )

        result = await use_case.execute()

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        _ = mock_restore.assert_awaited_once()
        assert result.unchanged == 1

    async def test_meta_repository_error(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=1,
                videos=[Video(deleted=True, slug="test", yt_id="test")],
            ),
        )
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            side_effect=MetaRepositoryError("Сервис недоступен", 500),
        )

        result = await use_case.execute()

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        assert result.unchanged == 1

    async def test_embeddable_check(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=1,
                videos=[Video(deleted=True, slug="test", yt_id="test")],
            ),
        )
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            side_effect=UnauthorizedError,
        )
        mock_is_embeddable = mocker.patch.object(
            use_case._youtube_data_api_repo,  # pyright: ignore[reportPrivateUsage]
            "is_embeddable",
            return_value=True,
        )

        result = await use_case.execute()

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        _ = mock_is_embeddable.assert_awaited_once_with("test")
        assert result.restored == 1

    async def test_youtube_data_api_repo_is_none(
        self, use_case: VideoCleanerUseCase, mocker: MockFixture
    ) -> None:
        mock_get_all = mocker.patch.object(
            use_case._video_repo,  # pyright: ignore[reportPrivateUsage]
            "get_all",
            return_value=VideoList(
                total_count=1,
                videos=[Video(deleted=True, slug="test", yt_id="test")],
            ),
        )
        mock_is_exists = mocker.patch.object(
            use_case._meta_repo,  # pyright: ignore[reportPrivateUsage]
            "is_exists",
            side_effect=UnauthorizedError,
        )
        mock_is_embeddable = mocker.spy(
            use_case._youtube_data_api_repo,  # pyright: ignore[reportPrivateUsage]
            "is_embeddable",
        )
        use_case._youtube_data_api_repo = None  # pyright: ignore[reportPrivateUsage]

        result = await use_case.execute()

        _ = mock_get_all.assert_awaited_once()
        _ = mock_is_exists.assert_awaited_once()
        _ = mock_is_embeddable.assert_not_awaited()
        assert result.unchanged == 1
