import logging
from typing import Annotated

import typer

logger = logging.getLogger(__name__)


def main() -> None:
    typer.run(clean)


def clean(
    main_api_url: Annotated[
        str, typer.Option(envvar="MAIN_API_URL", help="URL API работы с видео")
    ],
    yt_data_api_url: Annotated[
        str,
        typer.Option(
            envvar="YT_DATA_API_URL", help="URL API поставщика данных YouTube"
        ),
    ],
    limit: Annotated[
        int,
        typer.Option(
            envvar="LIMIT",
            help="Количество последних видео, которые нужно проверить",
        ),
    ] = 500,
) -> None:
    """
    Очистка видео. Если limit указан 0, то происходит проверка и очистка всех видео.
    """
    ...
