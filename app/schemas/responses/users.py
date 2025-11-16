from pydantic import Field

from app.models import Role

from .base import BaseResponse


class UserResponse(BaseResponse):
    username: str = Field(..., description="The username of the user")
    role: Role = Field(..., description="The role of the user")
    display_name: str | None = None
    email: str | None = None
    country_code: str | None = None
    total_credits: int = 0
    instagram_url: str | None = None
    youtube_url: str | None = None
    website_url: str | None = None

    class Config:
        from_attributes = True
