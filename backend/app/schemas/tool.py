from pydantic import BaseModel


class ToolRead(BaseModel):
    name: str
    description: str
    enabled: bool = True
