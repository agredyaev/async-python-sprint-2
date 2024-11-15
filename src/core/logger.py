import logging

from logging import config

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"verbose": {"format": LOG_FORMAT}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


def setup_logging() -> None:
    config.dictConfig(LOGGING)


setup_logging()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
