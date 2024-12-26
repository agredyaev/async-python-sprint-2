from collections.abc import Generator

import requests

from src.schemas.contex import Context
from src.schemas.response import ResponseData
from src.schemas.task import HttpTaskConfig
from src.task.base import BaseTask


class HttpTask(BaseTask):
    """Implementation of HTTP request task."""

    def __init__(self, config: HttpTaskConfig) -> None:
        """
        Initialize HTTP task.

        Args:
            config: HTTP task configuration
        """
        super().__init__(config)
        self._config: HttpTaskConfig = config

    def _do_execute(self, context: Context) -> Generator[None, None, None]:
        """
        Execute HTTP request based on configuration.

        Args:
            context: Task execution context
        """
        yield

        with requests.Session() as session:
            yield

            try:
                response = self._make_request(session)
                yield

                response.raise_for_status()
                yield

                self._store_results(context, response)

            except requests.RequestException as e:
                context.data["error"] = str(e)
                raise

        yield  # Final yield after session is closed

    def _make_request(self, session: requests.Session) -> requests.Response:
        """Make the HTTP request."""
        return session.request(
            method=self._config.method, url=self._config.url, headers=self._config.headers, timeout=self._config.timeout
        )

    def _store_results(self, context: Context, response: requests.Response) -> None:
        """Store the results of the HTTP request in the context."""
        context.results[str(self.task_id)] = ResponseData(
            status_code=response.status_code, headers=dict(response.headers), content=response.text
        ).model_dump()

        context.data["url"] = self._config.url
        context.data["method"] = self._config.method
