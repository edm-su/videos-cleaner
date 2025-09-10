from functools import partial
from typing import Annotated

import typer
from asyncer import syncify
from wireup import create_async_container

from videos_cleaner.adapters import repositories
from videos_cleaner.adapters.repositories.video_repository import VideoRepository
from videos_cleaner.domain.use_cases import video_use_case
from videos_cleaner.domain.use_cases.video_use_case import VideoCleanerUseCase

app = typer.Typer()
container = create_async_container(
    [repositories, video_use_case], parameters={"video_url": "http://localhost"}
)


@app.command()
@partial(syncify, raise_sync_error=False)
async def main(
    main_api_url: Annotated[
        str,
        typer.Option(envvar="MAIN_API_URL", help="URL API работы с видео"),
    ],
    limit: Annotated[
        int,
        typer.Option(
            envvar="LIMIT",
            help="Количество последних видео, которые нужно проверить",
        ),
    ] = 500,
) -> None:
    """Очистка видео. Если limit указан 0, то происходит очистка всех видео."""
    cleaner_use_case = await container.get(VideoCleanerUseCase)
    video_repository = await container.get(VideoRepository)

    video_repository.base_url = main_api_url

    result = await cleaner_use_case.execute(limit)

    print(f"""Обработано: {result.total} видео.
Скрыто: {result.hidden}.
Удалено навсегда: {result.deleted}.
Восстановлено: {result.restored}""")
    await container.close()


if __name__ == "__main__":
    app()
