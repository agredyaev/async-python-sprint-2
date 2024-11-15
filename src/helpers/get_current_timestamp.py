from datetime import UTC, datetime


def get_current_timestamp() -> datetime:
    return datetime.now(tz=UTC)
