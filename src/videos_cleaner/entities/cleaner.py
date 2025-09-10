from dataclasses import dataclass


@dataclass
class VideoCleanerStats:
    """Статистика выполнения очистки видео."""

    hidden: int = 0
    deleted: int = 0
    unchanged: int = 0
    restored: int = 0

    @property
    def total(self) -> int:
        """Всего обработано."""
        return self.hidden + self.deleted + self.unchanged + self.restored
