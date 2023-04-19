from pydantic import BaseModel 

class Config(BaseModel):
    token: str
    prefix: str
    disabled: list[str] | None = None

CONFIG: Config = None