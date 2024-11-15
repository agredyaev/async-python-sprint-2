from pydantic import BaseModel


class ResponseData(BaseModel):
    status_code: int
    headers: dict[str, str]
    content: str
