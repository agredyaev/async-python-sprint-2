import os
import re

from pathlib import Path

from pydantic import BaseModel, Field


class FileContent(BaseModel):
    relative_path: str = Field(..., description="Относительный путь к файлу")
    content: str = Field(..., description="Содержимое файла")


def concatenate_files(directories: list[Path], output_file: str) -> None:
    with open(output_file, "w", encoding="utf-8") as outfile:
        for directory in directories:
            for root, _, files in os.walk(directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    relative_path = os.path.relpath(filepath, directory)
                    try:
                        with open(filepath, encoding="utf-8") as infile:
                            content = infile.read()
                            file_content = FileContent(relative_path=relative_path, content=content)
                            pattern = re.compile(r"\s+")
                            sentence = f"##filename:{file_content.relative_path}#content_start:{file_content.content}content_end"
                            outfile.write(re.sub(pattern, "", sentence))
                    except Exception as e:
                        print(f"Ошибка при обработке файла {filepath}: {e!s}")


# Пример использования
directories = [Path().joinpath(Path().cwd(), dir_) for dir_ in ["src"]]
output_file = "output.txt"
concatenate_files(directories, output_file)
