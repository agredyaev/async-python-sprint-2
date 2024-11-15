from typing import Generator
from threading import RLock
from uuid import UUID
import time
from datetime import datetime, timedelta
from collections import deque

from pydantic import BaseModel

from src.core.settings import settings
from src.schemas import TaskState, TaskConfig, Pipeline
from src.protocols import (
    TaskPoolProtocol,
    ContextManagerProtocol,
    StateManagerProtocol,
    TaskFactoryProtocol,
    TaskProtocol
)
from src.core.exceptions import SchedulerError

class SchedulerStatus(BaseModel):
    is_running: bool
    active_coroutines: int
    last_maintenance: datetime

class Scheduler:
    """Main scheduler implementation using coroutines for task execution."""

    def __init__(
        self,
        task_pool: TaskPoolProtocol,
        context_manager: ContextManagerProtocol,
        state_manager: StateManagerProtocol,
        task_factory: TaskFactoryProtocol,
    ) -> None:
        self._task_pool = task_pool
        self._context_manager = context_manager
        self._state_manager = state_manager
        self._task_factory = task_factory
        self._config = settings.scheduler
        self._lock = RLock()
        self._status = SchedulerStatus(
            is_running=False,
            active_coroutines=0,
            last_maintenance=datetime.now()
        )
        self._active_coroutines: deque[Generator] = deque()

    def scheduler_loop(self) -> Generator[None, None, None]:
        """Main scheduler coroutine."""
        while self._status.is_running:
            try:
                task = yield from self._task_pool.get_next_task()
                if task:
                    task_coroutine = self._process_task(task)
                    self._active_coroutines.append(task_coroutine)
                yield
                self._process_coroutines()
            except Exception as e:
                print(f"Error in scheduler loop: {str(e)}")
            yield

    def _process_coroutines(self) -> None:
        """Process active coroutines."""
        for _ in range(min(len(self._active_coroutines), self._config.max_concurrent_tasks)):
            if not self._active_coroutines:
                break
            coroutine = self._active_coroutines.popleft()
            try:
                next(coroutine)
                self._active_coroutines.append(coroutine)
            except StopIteration:
                pass
            except Exception as e:
                print(f"Error in coroutine: {str(e)}")

    def _process_task(self, task: TaskProtocol) -> Generator[None, None, None]:
        """Process single task as a coroutine."""
        try:
            context = self._context_manager.get_context(task.task_id)
            yield from task.execute(context)
            self._context_manager.update_context(context)
            self._state_manager.update_task_state(task.task_id, TaskState.COMPLETED)
        except Exception as e:
            context.data['error'] = str(e)
            self._context_manager.update_context(context)
            self._state_manager.update_task_state(task.task_id, TaskState.FAILED)
        finally:
            yield from self._task_pool.remove_task(task.task_id)

    def maintenance_loop(self) -> Generator[None, None, None]:
        """Maintenance coroutine."""
        while self._status.is_running:
            try:
                current_time = datetime.now()
                if current_time - self._status.last_maintenance > timedelta(seconds=self._config.cleanup_interval):
                    yield from self._run_maintenance(current_time)
                    self._status.last_maintenance = current_time
                yield
            except Exception as e:
                print(f"Error in maintenance loop: {str(e)}")
            yield

    def _run_maintenance(self, current_time: datetime) -> Generator[None, None, None]:
        """Run maintenance operations as a coroutine."""
        cleanup_time = current_time - timedelta(seconds=self._config.cleanup_interval)
        try:
            yield from self._state_manager.cleanup_states(cleanup_time)
            yield from self._task_pool.cleanup_completed(cleanup_time)
            yield from self._state_manager.save_state()
        except Exception as e:
            print(f"Error during maintenance: {str(e)}")

    def run(self) -> None:
        """Run scheduler using coroutines."""
        with self._lock:
            if self._status.is_running:
                raise SchedulerError("Scheduler is already running")
            self._status.is_running = True

        try:
            self._state_manager.load_state()
            scheduler_gen = self.scheduler_loop()
            maintenance_gen = self.maintenance_loop()

            while self._status.is_running:
                next(scheduler_gen)
                next(maintenance_gen)
                time.sleep(self._config.state_check_interval)
        except Exception as e:
            raise SchedulerError(f"Scheduler error: {str(e)}") from e
        finally:
            self._status.is_running = False

    def stop(self) -> None:
        """Stop scheduler operation gracefully."""
        with self._lock:
            self._status.is_running = False
            self._state_manager.save_state()

    def schedule_task(self, config: TaskConfig) -> Generator[None, None, UUID]:
        """Schedule single task for execution."""
        try:
            task = self._task_factory.create_task(config)
            yield
            context = self._context_manager.create_context()
            self._context_manager.associate_task(task.task_id, context.context_id)
            yield
            yield from self._task_pool.add_task(task)
            self._state_manager.update_task_state(task.task_id, TaskState.PENDING)
            yield
            return task.task_id
        except Exception as e:
            raise SchedulerError(f"Failed to schedule task: {str(e)}") from e

    def schedule_pipeline(self, config: Pipeline) -> Generator[None, None, UUID]:
        """Schedule pipeline of tasks for execution."""
        try:
            pipeline_context = self._context_manager.create_context(config.pipeline_id)
            yield
            for task_config in config.tasks:
                task = self._task_factory.create_task(task_config)
                yield
                self._context_manager.associate_task(task.task_id, pipeline_context.context_id)
                yield
                yield from self._task_pool.add_task(task)
                self._state_manager.update_task_state(task.task_id, TaskState.PENDING)
                yield
            return config.pipeline_id
        except Exception as e:
            raise SchedulerError(f"Failed to schedule pipeline: {str(e)}") from e

    def get_task_status(self, task_id: UUID) -> dict:
        """Get current task status."""
        try:
            state = self._state_manager.get_task_state(task_id)
            context = self._context_manager.get_context(task_id)
            return {
                'task_id': task_id,
                'state': state.value,
                'results': context.results.get(str(task_id)),
                'error': context.data.get('error'),
                'updated_at': context.updated_at.isoformat()
            }
        except Exception as e:
            raise SchedulerError(f"Failed to get task status: {str(e)}") from e

    def get_pipeline_status(self, pipeline_id: UUID) -> dict:
        """Get pipeline status."""
        try:
            context = self._context_manager.get_pipeline_context(pipeline_id)
            return {
                'pipeline_id': pipeline_id,
                'tasks': context.results,
                'error': context.data.get('error'),
                'updated_at': context.updated_at.isoformat()
            }
        except Exception as e:
            raise SchedulerError(f"Failed to get pipeline status: {str(e)}") from e