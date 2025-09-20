set dotenv-load

lint:
    uv run ruff check
    uv run ruff format --check

format:
    uv run ruff format

type-check:
    uv run pyrefly check .

unit-tests:
    uv run pytest tests/units

integration-tests:
    uv run pytest tests/integration

coverage:
    uv run pytest tests/units --cov=src/videos_cleaner --cov-report=html
