from typing import Annotated, final

import structlog
from wireup import Inject, service

from videos_cleaner.domain.interfaces.meta_repository import (
    ExistsStatus,
    IMetaRepository,
    MetaRepositoryError,
    UnauthorizedError,
)
from videos_cleaner.domain.interfaces.video_repository import (
    IVideoRepository,
    VideoRepostiryError,
)
from videos_cleaner.entities.cleaner import VideoCleanerStats
from videos_cleaner.entities.video import Video

logger = structlog.stdlib.get_logger(__name__)


class RepositoryAlreadyInstalledError(ValueError):
    """Ошибка уже установленного репозитория."""

    def __init__(self) -> None:
        super().__init__("Репозиторий уже установлен")


@final
@service
class VideoCleanerUseCase:
    """UseCase чистильщика видео."""

    def __init__(
        self,
        video_repo: IVideoRepository,
        meta_repo: IMetaRepository,
        youtube_data_api_repo: Annotated[
            IMetaRepository | None, Inject(param="youtube_data_api_repo")
        ],
    ) -> None:
        """Конструктор.

        Args:
            video_repo: Репозиторий видео.
            meta_repo: Репозиторий информации о youtube видео.
            youtube_data_api_repo: Репозиторий Youtube Data API.
        """
        self._video_repo = video_repo
        self._meta_repo = meta_repo
        self._youtube_data_api_repo = youtube_data_api_repo
        self.batch_size = 50

    @property
    def youtube_data_api_repo(self) -> IMetaRepository | None:
        """Получить YouTube Data API репозиторий."""
        return self._youtube_data_api_repo

    @youtube_data_api_repo.setter
    def youtube_data_api_repo(self, new_value: IMetaRepository | None) -> None:
        if self._youtube_data_api_repo:
            raise RepositoryAlreadyInstalledError
        self._youtube_data_api_repo = new_value

    async def _process_video(
        self,
        video: Video,
        status: ExistsStatus,
        stats: VideoCleanerStats,
    ) -> None:
        """Обработать одно видео."""
        if video.deleted and status == ExistsStatus.EXISTS:
            await self._video_repo.restore(video.slug)
            stats.restored += 1
        elif video.deleted and status == ExistsStatus.REMOVED:
            await self._video_repo.delete(video.slug, temporary=False)
            stats.deleted += 1
        elif not video.deleted and status != ExistsStatus.EXISTS:
            await self._video_repo.delete(
                video.slug, temporary=status == ExistsStatus.HIDDEN
            )

            if status == ExistsStatus.HIDDEN:
                stats.hidden += 1
            else:
                stats.deleted += 1
        else:
            stats.unchanged += 1

    async def execute(self, limit: int | None = None) -> VideoCleanerStats:
        """Выполнить очистку.

        Args:
            limit: Ограничение на общее количество (None значит не ограничен).

        Returns:
            VideoCleanerStats: статистика выполнения.
        """
        offset = 0
        stats = VideoCleanerStats()

        while True:
            videos = await self._video_repo.get_all(offset, limit=self.batch_size)
            total_counter = videos.total_count

            for video in videos.videos:
                try:
                    status = await self._meta_repo.is_exists(video.yt_id)
                    await self._process_video(video, status, stats)

                except UnauthorizedError:
                    logger.debug("Доступ не авторизован", yt_id=video.yt_id)

                    if self._youtube_data_api_repo:
                        status = (
                            ExistsStatus.EXISTS
                            if await self._youtube_data_api_repo.is_embeddable(
                                video.yt_id
                            )
                            else ExistsStatus.HIDDEN
                        )
                        await self._process_video(video, status, stats)
                    else:
                        stats.unchanged += 1
                except MetaRepositoryError:
                    logger.exception("Ошибка мета репозитория", yt_id=video.yt_id)
                    stats.unchanged += 1
                except VideoRepostiryError:
                    logger.exception("Ошибка видео репозитория", slug=video.slug)
                    stats.unchanged += 1

                if limit and stats.total >= limit:
                    return stats

            offset += self.batch_size

            if offset >= total_counter:
                break

        return stats
