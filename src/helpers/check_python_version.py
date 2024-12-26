from typing import Any, TypeVar, cast

import sys

from collections.abc import Callable
from functools import wraps

from src.core.exceptions import UnsupportedPythonVersionError
from src.core.settings import settings

F = TypeVar("F", bound=Callable[..., Any])


def requires_python_version() -> Callable[[F], F]:
    min_major = settings.py_ver.min_major
    min_minor = settings.py_ver.min_minor

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if sys.version_info.major < min_major or (
                sys.version_info.major == min_major and sys.version_info.minor < min_minor
            ):
                raise UnsupportedPythonVersionError(f"Required python version >= {min_major}.{min_minor}.")
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
