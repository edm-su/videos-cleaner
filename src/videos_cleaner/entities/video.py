from pydantic import BaseModel


class Video(BaseModel):
    deleted: bool
    slug: str
    yt_id: str


class VideoList(BaseModel):
    total_count: int
    videos: list[Video]
