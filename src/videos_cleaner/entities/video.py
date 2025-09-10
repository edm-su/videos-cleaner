from pydantic import BaseModel


class Video(BaseModel):
    """Инфомация о видео."""

    deleted: bool
    slug: str
    yt_id: str


class VideoList(BaseModel):
    """Список видео и общее количество видео."""

    total_count: int
    videos: list[Video]
