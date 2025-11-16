from datetime import datetime

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    id: int = Field(..., description="The unique identifier for this record")
    created_at: datetime = Field(
        ..., description="The date and time this record was created"
    )
    updated_at: datetime = Field(
        ..., description="The date and time this record was last updated"
    )

    class Config:
        from_attributes = True
