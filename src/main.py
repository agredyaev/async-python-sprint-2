from schemas import TaskType
from src.helpers import requires_python_version
from src.core.logger import get_logger
from src.schemas import TaskConfig
from src.task.factory import TaskFactory
from src.task.pool import TaskPool
from src.scheduler import Scheduler
from src.context import ContextManager
from src.state import FileStateManager


@requires_python_version()
def main() -> None:
    logger = get_logger(__name__)
    logger.info("Initializing task scheduler")

    task_factory = TaskFactory()
    task_pool = TaskPool()
    context_manager = ContextManager()
    state_manager = FileStateManager()

    scheduler = Scheduler(
        task_pool=task_pool,
        context_manager=context_manager,
        state_manager=state_manager,
        task_factory=task_factory,
    )

    file_task = TaskConfig(
        task_type=TaskType.FILE,
        task_specific_config={
            "operation": "READ",
            "file_path": "file.txt"
        }
    )
    http_task = TaskConfig(
        task_type=TaskType.HTTP,
        task_specific_config={
            "url": "https://api.example.com/data",
            "method": "GET"
        }
    )

    scheduler.schedule_task(file_task)
    scheduler.schedule_task(http_task)


    try:
        logger.info("Starting scheduler")
        scheduler.run()
    except KeyboardInterrupt:
        logger.info("Stopping scheduler")
        scheduler.stop()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        logger.info("Scheduler stopped")

if __name__ == "__main__":
    main()