#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Please specify the new version as an argument."
    echo "Usage: $0 <new_version>"
    exit 1
fi

NEW_VERSION=$1
PYPROJECT_TOML="pyproject.toml"

if [ ! -f "$PYPROJECT_TOML" ]; then
    echo "File $PYPROJECT_TOML not found."
    exit 1
fi


# Обновляем версию в pyproject.toml с помощью sed
sed -i.bak "s/version = \"[^\"]*\"/version = \"$NEW_VERSION\"/" "$PYPROJECT_TOML"

# Обновление версии uv.lock
uv lock

# Проверка успешности операции
if [ $? -eq 0 ]; then
    echo "Version updated successfully to $NEW_VERSION"
    rm -f "$PYPROJECT_TOML.bak"
    exit 0
else
    echo "Error updating version"
    exit 1
fi

