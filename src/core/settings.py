from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(find_dotenv())


class DefaultSettings(BaseSettings):
    """Class to store default project settings."""

    root_path: Path = Path().cwd().parent.parent.resolve()

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class PythonVersionSettings(DefaultSettings):
    """Class to store Python version settings."""

    min_major: int = Field(default=3, description="Minimum major version")
    min_minor: int = Field(default=9, description="Minimum minor version")

    model_config = SettingsConfigDict(env_prefix="PYTHON_")


class SchedulerConfig(DefaultSettings):
    """Global scheduler configuration parameters."""

    max_concurrent_tasks: int = Field(default=10, ge=1, description="Maximum concurrent tasks")
    default_task_timeout: float = Field(default=60.0, ge=0, description="Default task timeout in seconds")
    state_check_interval: float = Field(default=1.0, ge=0.1, description="State check interval in seconds")
    cleanup_interval: float = Field(default=3600.0, ge=0, description="Cleanup interval in seconds")

    model_config = SettingsConfigDict(env_prefix="SCHEDULER")


class PipelineConfig(DefaultSettings):
    """Configuration for task pipeline execution."""

    max_parallel: int = Field(default=1, ge=1, description="Maximum parallel tasks")
    timeout: float = Field(default=3600.0, ge=0, description="Pipeline timeout in seconds")

    model_config = SettingsConfigDict(env_prefix="PIPELINE")


class StateConfig(DefaultSettings):
    """Configuration for state."""

    version: int = Field(default=1, ge=1, description="State version")
    cache_size: int = Field(default=100, ge=1, description="Default cache size")
    save_interval: int = Field(default=60, ge=0, description="Default lock timeout in seconds")
    file_path: Path = Field(default=Path.cwd() / "test_state", description="State file path")

    model_config = SettingsConfigDict(env_prefix="STATE")


class Settings(BaseSettings):
    py_ver: PythonVersionSettings = PythonVersionSettings()
    scheduler: SchedulerConfig = SchedulerConfig()
    pipeline: PipelineConfig = PipelineConfig()
    state: StateConfig = StateConfig()


settings = Settings()
