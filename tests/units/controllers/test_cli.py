from typing import TYPE_CHECKING, cast

import structlog
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from videos_cleaner.adapters.repositories.meta_repository import (
    YoutubeDataApiRepository,
)
from videos_cleaner.controller.cli import app, container
from videos_cleaner.domain.use_cases.video_use_case import VideoCleanerUseCase
from videos_cleaner.entities.cleaner import VideoCleanerStats

if TYPE_CHECKING:
    from collections.abc import Callable

runner = CliRunner()


class TestCliController:
    def test_clean(self, mocker: MockerFixture) -> None:
        # Given
        stats = VideoCleanerStats(0, 0, 1, 0)
        mock_use_case = mocker.AsyncMock(spec=VideoCleanerUseCase)
        mock_execute = mocker.AsyncMock(return_value=stats)
        mock_use_case.execute = cast(
            "Callable[[int | None], VideoCleanerStats]", mock_execute
        )

        async def mock_get(_service: VideoCleanerUseCase) -> VideoCleanerUseCase:
            return mock_use_case

        _ = mocker.patch.object(container, "get", side_effect=mock_get)

        mock_logger = mocker.Mock()
        mock_logger.info = mocker.Mock()
        mock_get_logger = mocker.patch.object(
            structlog.stdlib, "get_logger", return_value=mock_logger
        )

        # When
        result = runner.invoke(app, ["--main-api-url", "http://test"])

        # Then
        mock_get_logger.assert_called_once()
        mock_logger.info.assert_called_once_with(
            "Обработка видео завершена",
            total=stats.total,
            hidden=stats.hidden,
            deleted=stats.deleted,
            restored=stats.restored,
        )
        assert result.exit_code == 0

    def test_with_youtube_data_api_key(self, mocker: MockerFixture) -> None:
        # Given
        stats = VideoCleanerStats(0, 0, 1, 0)
        mock_use_case = mocker.AsyncMock(spec=VideoCleanerUseCase)
        mock_execute = mocker.AsyncMock(return_value=stats)
        mock_use_case.execute = cast(
            "Callable[[int | None], VideoCleanerStats]", mock_execute
        )

        async def mock_get(_service: VideoCleanerUseCase) -> VideoCleanerUseCase:
            return mock_use_case

        _ = mocker.patch.object(container, "get", side_effect=mock_get)

        mock_repository = mocker.MagicMock(spec=YoutubeDataApiRepository)
        mock_repo_constructor = mocker.patch(
            "videos_cleaner.controller.cli.YoutubeDataApiRepository",
            return_value=mock_repository,
        )

        # When
        result = runner.invoke(
            app,
            [
                "--main-api-url",
                "http://test",
                "--youtube-data-api-key",
                "secretkey",
            ],
        )

        # Then
        mock_repo_constructor.assert_called_once_with(
            "secretkey", *mock_repo_constructor.call_args[0][1:]
        )
        assert result.exit_code == 0
