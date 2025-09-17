from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock

from pytest_mock import MockerFixture
from typer.testing import CliRunner

from videos_cleaner.controller.cli import app, container
from videos_cleaner.domain.use_cases.video_use_case import VideoCleanerUseCase
from videos_cleaner.entities.cleaner import VideoCleanerStats

if TYPE_CHECKING:
    from collections.abc import Callable

runner = CliRunner()


class TestCliController:
    def test_clean(self, mocker: MockerFixture) -> None:
        stats = VideoCleanerStats(0, 0, 1, 0)
        mock_use_case = AsyncMock(spec=VideoCleanerUseCase)
        mock_execute = AsyncMock(return_value=stats)
        mock_use_case.execute = cast(
            "Callable[[int | None], VideoCleanerStats]", mock_execute
        )

        async def mock_get(_service: VideoCleanerUseCase) -> VideoCleanerUseCase:
            return mock_use_case

        _ = mocker.patch.object(container, "get", side_effect=mock_get)

        result = runner.invoke(app, ["--main-api-url", "http://test"])

        assert (
            f"""Обработано: {stats.total} видео.
Скрыто: {stats.hidden}.
Удалено навсегда: {stats.deleted}.
Восстановлено: {stats.restored}"""
            in result.output
        )
        assert result.exit_code == 0
