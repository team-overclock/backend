from pydantic import BaseModel, EmailStr

from .common import Password, OptionalEmail, RegionName


class UserInfo(BaseModel):
    cuid: str
    name: str
    email: EmailStr
    region_id: int | None
    region_name: RegionName | None


class UserInfoUpdateRequest(BaseModel):
    name: str | None = None
    email: OptionalEmail = None
    region_id: int | None = None

class UserPasswordChangeRequest(BaseModel):
    current_password: str
    new_password: Password
