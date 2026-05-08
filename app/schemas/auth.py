from pydantic import BaseModel, Field, EmailStr

from .common import UserName, Password


class UserLoginRequest(BaseModel):
    email: str  # DB 필드명과 일치시킴
    password: str


class UserCreateRequest(BaseModel):
    name: UserName
    email: EmailStr
    password: Password
    region_id: int | None = Field(None, description="동네 ID")


class UserSession(BaseModel):
    cuid: str
