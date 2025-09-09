from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import override


class MetaRepositoryError(Exception):
    def __init__(self, message: str, code: int) -> None:
        self.message: str = message
        self.code: int = code
        super().__init__(message)

    @override
    def __str__(self) -> str:
        return f"Код ошибки: {self.code}. Детали: {self.message}"


class ExistsStatus(Enum):
    EXISTS = auto()
    HIDDEN = auto()
    REMOVED = auto()


class IMetaRepository(ABC):
    @abstractmethod
    async def is_exists(self, yt_id: str) -> ExistsStatus: ...
