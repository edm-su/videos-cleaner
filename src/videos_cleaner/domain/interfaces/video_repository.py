from abc import ABC, abstractmethod
from typing import final, override

from videos_cleaner.entities.video import VideoList


class VideoRepostiryError(Exception):
    def __init__(self, message: str, code: int) -> None:
        self.message: str = message
        self.code: int = code
        super().__init__(message)

    @override
    def __str__(self) -> str:
        return f"Код ошибки: {self.code}. Детали: {self.message}"


@final
class VideoNotFoundError(VideoRepostiryError):
    def __init__(self) -> None:
        self.message = "Видео не найдено"
        self.code = 404
        super().__init__(self.message, self.code)


@final
class VideoIsAlreadyDeletedError(VideoRepostiryError):
    def __init__(self) -> None:
        self.message = "Видео было уже удалено"
        self.code = 409
        super().__init__(self.message, self.code)


@final
class VideoIsNotDeletedError(VideoRepostiryError):
    def __init__(self) -> None:
        self.message = "Видео не может быть удалено"
        self.code = 409
        super().__init__(self.message, self.code)


class IVideoRepository(ABC):
    @abstractmethod
    async def get_all(self, offset: int = 0, *, limit: int = 50) -> VideoList: ...

    @abstractmethod
    async def delete(self, slug: str, *, temporary: bool = True) -> None: ...

    @abstractmethod
    async def restore(self, slug: str) -> None: ...
