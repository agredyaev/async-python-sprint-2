from src.core.logger import get_logger
from src.helpers import requires_python_version

logger = get_logger(__name__)


@requires_python_version()
def main() -> None:
    logger.info("Initializing task scheduler")


if __name__ == "__main__":
    main()
