from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from .common import PK_STR, Password, OptionalEmail


class UserInfo(BaseModel):
    cuid: PK_STR
    name: str
    email: EmailStr
    created_at: datetime = Field(description="사용자 등록 일시")


class UserInfoUpdateRequest(BaseModel):
    name: str | None = None
    email: OptionalEmail = None

class UserPasswordChangeRequest(BaseModel):
    current_password: str
    new_password: Password
