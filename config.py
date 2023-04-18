from pydantic import BaseModel 

class Config(BaseModel):
    token: str
    prefix: str
    disabled: list[str]

CONFIG: Config = None