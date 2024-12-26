import os
import re

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from src.core.logger import get_logger

logger = get_logger("content")


class FileContent(BaseModel):
    relative_path: str = Field(..., description="Относительный путь к файлу")
    content: str = Field(..., description="Содержимое файла")


def concatenate_files(directories: list[Path], output_file: str) -> None:
    with Path(output_file).open(mode="w", encoding="utf-8") as outfile:
        for directory in directories:
            for root, _, files in os.walk(directory):
                for filename in files:
                    filepath = Path(root) / filename
                    relative_path = os.path.relpath(filepath, directory)
                    try:
                        with Path(filepath).open(encoding="utf-8") as infile:
                            content = infile.read()
                            file_content = FileContent(relative_path=relative_path, content=content)
                            pattern = re.compile(r"\s+")
                            sentence = f"#filename:{file_content.relative_path}#content_start:{file_content.content}content_end"
                            outfile.write(re.sub(pattern, "", sentence))
                    except Exception as e:
                        logger.exception("Ошибка при обработке файла", exc_info=e)


directories = [Path().joinpath(Path().cwd(), dir_) for dir_ in ["src"]]
output_file = "output.txt"
concatenate_files(directories, output_file)
logger.info("Файл %s успешно создан datetime:%s", output_file, datetime.now(tz=UTC))
