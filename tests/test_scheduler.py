from collections.abc import Generator
from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from polyfactory.factories.pydantic_factory import ModelFactory
from pytest_mock import MockerFixture

from src.helpers import get_current_timestamp
from src.scheduler import Scheduler
from src.schemas import Context, FileTaskConfig, TaskState
from src.task import BaseTask


class BaseFactory:
    __random_seed__ = 1


class BaseTaskFactory(BaseFactory, ModelFactory[FileTaskConfig]): ...


@pytest.fixture
def mock_context_manager(mocker: MockerFixture):
    return mocker.Mock()


@pytest.fixture
def mock_state_manager(mocker: MockerFixture):
    return mocker.Mock()


@pytest.fixture
def scheduler(mock_context_manager, mock_state_manager):
    return Scheduler(mock_context_manager, mock_state_manager)


class FBaseTask(BaseTask):
    def _do_execute(self, context: Context) -> Generator[None, None, None]:
        """Simulate a task that always fails."""
        yield None


class TestScheduler:
    def test_add_task(self, scheduler, mocker: MockerFixture):
        config = BaseTaskFactory.build()
        task = FBaseTask(config)

        mock_context = mocker.Mock()
        scheduler._context_manager.create_context.return_value = iter([mock_context])
        scheduler._context_manager.associate_task.return_value = iter([None])

        scheduler.add_task(task)

        assert len(scheduler._tasks) == 1, "Task was not added to the queue"
        assert scheduler._tasks[0] == task, "Added task is not at the front of the queue"

    def test_can_execute_start_time_not_reached(self, scheduler, mocker: MockerFixture):
        future_time = get_current_timestamp() + timedelta(hours=1)
        config = BaseTaskFactory.build(start_time=future_time.timestamp())
        task = FBaseTask(config)

        mocker.patch("src.helpers.get_current_timestamp", return_value=get_current_timestamp().timestamp())

        assert not scheduler._can_execute(task), "Task should not be executable before start time"

    def test_can_execute_dependencies_completed(self, scheduler):
        dependency = uuid4()
        config = BaseTaskFactory.build(dependencies=[dependency])
        task = FBaseTask(config)
        scheduler._completed_tasks.add(dependency)

        assert scheduler._can_execute(task), "Task should be executable if all dependencies are completed"

    def test_can_execute_dependencies_failed(self, scheduler, mocker: MockerFixture):
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        future_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=1)

        dependency = uuid4()
        config = BaseTaskFactory.build(dependencies=[dependency], start_time=future_time)
        task = FBaseTask(config)
        scheduler._failed_tasks.add(dependency)

        mock_context = mocker.Mock()
        scheduler._context_manager.create_context.return_value = iter([mock_context])
        scheduler._context_manager.associate_task.return_value = iter([None])

        scheduler.add_task(task)
        list(scheduler.run())

        assert task.task_id in scheduler._failed_tasks, "Task should be added to failed tasks"
        assert task not in scheduler._tasks, "Task should be removed from the queue"
        assert task.state == TaskState.FAILED, "Task state should be set to FAILED"

    def test_run(self, scheduler, mocker: MockerFixture):
        config1 = BaseTaskFactory.build(start_time=None)
        task1 = FBaseTask(config1)
        config2 = BaseTaskFactory.build(start_time=None, dependencies=[task1.task_id])
        task2 = FBaseTask(config2)
        scheduler._tasks.extend([task1, task2])

        mocker.patch.object(scheduler, "_can_execute", side_effect=[True, False, True])
        mocker.patch.object(scheduler, "_process_task", return_value=iter([None]))

        list(scheduler.run())

        assert len(scheduler._tasks) == 0, "Tasks should be removed from the queue"
        assert scheduler._process_task.call_count == 2, "Task should be processed twice"

    def test_context_manager(self, scheduler, mocker: MockerFixture):
        mock_load = mocker.patch.object(scheduler._state_manager, "load", return_value=iter([None]))
        mock_save = mocker.patch.object(scheduler._state_manager, "save", return_value=iter([None]))

        with scheduler:
            pass

        mock_load.assert_called_once(), "State manager should be loaded"
        mock_save.assert_called_once(), "State manager should be saved"
