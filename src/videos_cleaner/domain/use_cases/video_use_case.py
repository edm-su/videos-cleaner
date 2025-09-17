import logging
from typing import final

from wireup import service

from videos_cleaner.domain.interfaces.meta_repository import (
    ExistsStatus,
    IMetaRepository,
    MetaRepositoryError,
)
from videos_cleaner.domain.interfaces.video_repository import (
    IVideoRepository,
    VideoRepostiryError,
)
from videos_cleaner.entities.cleaner import VideoCleanerStats
from videos_cleaner.entities.video import Video


@final
@service
class VideoCleanerUseCase:
    """UseCase чистильщика видео."""

    def __init__(
        self,
        video_repo: IVideoRepository,
        meta_repo: IMetaRepository,
    ) -> None:
        """Конструктор.

        Args:
            video_repo: Репозиторий видео.
            meta_repo: Репозиторий информации о youtube видео.
        """
        self._video_repo = video_repo
        self._meta_repo = meta_repo
        self.logger = logging.getLogger("VideoCleanerUseCase")
        self.batch_size = 50

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
                except MetaRepositoryError:
                    self.logger.exception("Ошибка мета репозитория")
                    stats.unchanged += 1
                except VideoRepostiryError:
                    self.logger.exception("Ошибка видео репозитория")
                    stats.unchanged += 1

                if limit and stats.total >= limit:
                    return stats

            offset += self.batch_size

            if offset >= total_counter:
                break

        return stats
