from pydantic import BaseModel, EmailStr

from .common import PK_STR, OptionalStr, Password
from .user import UserInfo


class LoginCheckResponse(BaseModel):
    is_logged_in: bool
    user: UserInfo | None


class UserLoginRequest(BaseModel):
    email: str  # DB 필드명과 일치시킴
    password: str


class UserCreateRequest(BaseModel):
    name: OptionalStr = None
    email: EmailStr
    password: Password


class UserSession(BaseModel):
    cuid: PK_STR
