from pydantic import BaseModel, Field


class Health(BaseModel):
    version: str = Field(..., example="0.0.1")
    status: str = Field(..., example="OK")
