from src.context import ContextManager
from src.core.logger import get_logger
from src.helpers import requires_python_version
from src.scheduler import Scheduler
from src.schemas import FileOperation
from src.schemas.task import FileTaskConfig, HttpTaskConfig
from src.state import FileStateManager
from src.task import TaskRegistry

logger = get_logger(__name__)


@requires_python_version()
def main() -> None:
    registry = TaskRegistry()
    context_manager = ContextManager()
    state_manager = FileStateManager()
    scheduler = Scheduler(context_manager=context_manager, state_manager=state_manager)

    file_config = FileTaskConfig(operation=FileOperation.WRITE, file_path="test_file.txt", content="Hello, world!")
    file_task = next(registry.create_task(file_config))

    http_config = HttpTaskConfig(url="https://catfact.ninja/fact")
    http_task = next(registry.create_task(http_config))

    parent_http_config = HttpTaskConfig(url="https://catfact.ninja/fact")
    parent_http_task = next(registry.create_task(parent_http_config))

    dependent_file_config = FileTaskConfig(operation=FileOperation.READ, file_path="test_file.txt")
    dependent_file_task = next(registry.create_task(dependent_file_config))

    with scheduler:
        scheduler.add_task(file_task)
        scheduler.add_task(http_task)

        scheduler.add_task(parent_http_task)
        scheduler.add_task(dependent_file_task)

        list(scheduler.run())


if __name__ == "__main__":
    main()
