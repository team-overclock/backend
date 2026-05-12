from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

from .common import UserName, Password, RegionName


class UserLoginRequest(BaseModel):
    email: str  # DB 필드명과 일치시킴
    password: str


class UserCreateRequest(BaseModel):
    name: UserName
    email: EmailStr
    password: Password
    region_id: int | None = Field(None, description="동네 ID")

class UserCreateResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    region_id: int | None
    region_name: RegionName | None
    created_at: datetime


class UserSession(BaseModel):
    cuid: str
