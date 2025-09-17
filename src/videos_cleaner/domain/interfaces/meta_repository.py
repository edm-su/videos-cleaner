from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import override

from wireup import abstract


class MetaRepositoryError(Exception):
    """Ошибка репозитория мета информации о Youtube видео."""

    def __init__(self, message: str, code: int) -> None:
        self.message: str = message
        self.code: int = code
        super().__init__(message)

    @override
    def __str__(self) -> str:
        return f"Код ошибки: {self.code}. Детали: {self.message}"


class ExistsStatus(Enum):
    """Статус существования."""

    EXISTS = auto()
    HIDDEN = auto()
    REMOVED = auto()


@abstract
class IMetaRepository(ABC):
    """Репозиторий мета информации о Youtube видео."""

    @abstractmethod
    async def is_exists(self, yt_id: str) -> ExistsStatus:
        """Проверка существования видео в youtube.

        Args:
            yt_id: идентификатор youtube видео.

        Raises:
            MetaRepositoryError: общая ошибка репозитория.
        """
