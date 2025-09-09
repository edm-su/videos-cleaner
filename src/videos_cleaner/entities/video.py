from pydantic import BaseModel


class Video(BaseModel):
    slug: str
    deleted: bool


class VideoList(BaseModel):
    total_count: int
    videos: list[Video]
