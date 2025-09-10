from abc import ABC, abstractmethod
from typing import final, override

from wireup import abstract

from videos_cleaner.entities.video import VideoList


class VideoRepostiryError(Exception):
    """Общая ошибка репозитория."""

    def __init__(self, message: str, code: int) -> None:
        self.message: str = message
        self.code: int = code
        super().__init__(message)

    @override
    def __str__(self) -> str:
        return f"Код ошибки: {self.code}. Детали: {self.message}"


@final
class VideoNotFoundError(VideoRepostiryError):
    """Видео не найдено."""

    def __init__(self) -> None:
        self.message = "Видео не найдено"
        self.code = 404
        super().__init__(self.message, self.code)


@final
class VideoIsAlreadyDeletedError(VideoRepostiryError):
    """Видео уже удалено."""

    def __init__(self) -> None:
        self.message = "Видео было уже удалено"
        self.code = 409
        super().__init__(self.message, self.code)


@final
class VideoIsNotDeletedError(VideoRepostiryError):
    """Видео не было удалено ранее."""

    def __init__(self) -> None:
        self.message = "Видео не может быть удалено"
        self.code = 409
        super().__init__(self.message, self.code)


@abstract
class IVideoRepository(ABC):
    """Интерфейс репозитория видео."""

    @abstractmethod
    async def get_all(self, offset: int = 0, *, limit: int = 50) -> VideoList:
        """Получить все элементы (с пагинацией).

        Args:
            offset: Отступ.
            limit: Ограничение на количество.

        Returns:
            Возвращает VideoList со списком видео.

        Raises:
            VideoRepositoryError: Неизвестная ошибка.
        """
        ...

    @abstractmethod
    async def delete(self, slug: str, *, temporary: bool = True) -> None:
        """Удалить видео.

        Args:
            slug: Идентификатор видео.
            temporary: Удалить временно/навсегда (по умолчанию временно).

        Raises:
            VideosIsAlreadyDeletedError:
            VideoNotFoundError:
            VideoRepositoryError:
        """
        ...

    @abstractmethod
    async def restore(self, slug: str) -> None:
        """Восстановить видео.

        Args:
            slug: Идентификатор видео.

        Raises:
            VideosIsNoteDeletedError:
            VideoNotFoundError:
            VideoRepositoryError:
        """
        ...
