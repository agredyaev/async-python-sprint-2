from collections.abc import Generator
from uuid import UUID

import pytest

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import ValidationError
from pytest_mock import MockerFixture

from src.core.exceptions import BaseTaskError, TaskError, TaskMaxRetriesError, TaskTypeNotFoundError
from src.schemas import Context, FileOperation, FileTaskConfig, HttpTaskConfig, TaskConfig, TaskState, TaskType
from src.task import BaseTask, FileTask, HttpTask
from src.task.factory import TaskImplementation, TaskRegistry


class BaseFactory:
    __random_seed__ = 1


class TaskConfigFactory(BaseFactory, ModelFactory[TaskConfig]): ...


class HttpTaskConfigFactory(BaseFactory, ModelFactory[HttpTaskConfig]): ...


class FileTaskConfigFactory(BaseFactory, ModelFactory[FileTaskConfig]): ...


@pytest.fixture
def task_registry():
    return TaskRegistry()


class TestTaskRegistry:
    def test_create_http_task(self, task_registry):
        config = HttpTaskConfigFactory.build(task_type=TaskType.HTTP)
        task = next(task_registry.create_task(config))
        assert isinstance(task, HttpTask), "Task is not an HttpTask"
        assert task.task_id == config.id, "Task ID does not match"

    def test_create_file_task(self, task_registry):
        config = FileTaskConfigFactory.build(task_type=TaskType.FILE)
        task = next(task_registry.create_task(config))
        assert isinstance(task, FileTask), "Task is not a FileTask"
        assert task.task_id == config.id, "Task ID does not match"

    def test_create_task_with_invalid_type(self, task_registry):
        with pytest.raises(ValidationError):
            TaskConfigFactory.build(task_type="INVALID_TYPE")

    def test_http_task_execution(self, mocker: MockerFixture):
        config = HttpTaskConfigFactory.build(
            url="https://example.com", method="GET", headers={"Authorization": "Bearer token"}
        )
        task = HttpTask(config)

        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"key": "value"}'

        mock_session = mocker.Mock()
        mock_session.request.return_value = mock_response
        mock_session.__enter__ = mocker.Mock(return_value=mock_session)
        mock_session.__exit__ = mocker.Mock(return_value=None)

        mocker.patch("requests.Session", return_value=mock_session)

        context = mocker.Mock()
        context.results = {}
        context.data = {}

        list(task._do_execute(context))

        assert context.results[str(task.task_id)]["status_code"] == 200, "Status code does not match"
        assert context.data["url"] == config.url, "URL does not match"
        assert context.data["method"] == config.method, "Method does not match"

    def test_file_task_execution(self, mocker: MockerFixture, tmp_path):
        test_file = tmp_path / "test.txt"

        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        future_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=1)

        config = FileTaskConfigFactory.build(
            file_path=str(test_file), operation=FileOperation.WRITE, content="Test content", start_time=future_time
        )
        task = FileTask(config)

        context = mocker.Mock()
        context.results = {}
        context.data = {}

        list(task._do_execute(context))

        assert test_file.read_text() == "Test content", "File content does not match"
        assert context.data["file_path"] == str(test_file), "File path does not match"
        assert context.data["operation"] == FileOperation.WRITE.value, "Operation does not match"

    def test_file_task_read_operation(self, tmp_path, mocker: MockerFixture):
        test_file = tmp_path / "test.txt"
        test_content = "Test content"
        test_file.write_text(test_content)

        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        future_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=1)

        config = FileTaskConfigFactory.build(
            file_path=str(test_file), operation=FileOperation.READ, start_time=future_time
        )
        task = FileTask(config)
        context = mocker.Mock()
        context.results = {}
        context.data = {}

        list(task._do_execute(context))

        assert context.results[str(task.task_id)] == test_content, "File content does not match"
        assert context.data["operation"] == FileOperation.READ.value, "Operation does not match"

    def test_file_task_append_operation(self, tmp_path, mocker: MockerFixture):
        test_file = tmp_path / "test.txt"
        initial_content = "Initial content\n"
        test_file.write_text(initial_content)

        config = FileTaskConfigFactory.build(
            file_path=str(test_file), operation=FileOperation.APPEND, content="Appended content"
        )
        task = FileTask(config)
        context = mocker.Mock()
        context.results = {}
        context.data = {}

        list(task._do_execute(context))

        assert test_file.read_text() == initial_content + "Appended content", "File content does not match"
        assert context.data["operation"] == FileOperation.APPEND.value, "Operation does not match"

    def test_task_retry_logic(self, mocker: MockerFixture):
        """Checks if the task retry logic works as expected."""

        max_retries = 3
        config = HttpTaskConfigFactory.build(max_retries=max_retries)

        class FailingTask(BaseTask):
            def _do_execute(self, context: Context) -> Generator[None, None, None]:
                """Simulate a task that always fails."""
                raise BaseTaskError("Simulated failure")

        task = FailingTask(config)
        context = mocker.Mock()

        with pytest.raises(TaskMaxRetriesError, match="Task max retries exceeded"):
            list(task.execute(context))

        assert task.state == TaskState.FAILED, "Task did not end in FAILED state"
        assert task.metrics.retry_count == max_retries, "Retry count does not match max_retries"
        assert task._error is not None, "Task error is not set after failure"

        assert task._error.message == "Simulated failure", "Task error message does not match"

        assert task._error.timestamp is not None, "Task error timestamp is missing"
        assert task._end_time.second == task._error.timestamp.second, "End time does not match error timestamp"
