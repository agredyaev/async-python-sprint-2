from typing import Any

from pathlib import Path

from pydantic_core import from_json


def from_json_file(path: str) -> dict[str, Any]:
    with Path(path).open("rb") as file:
        return from_json(file.read())
