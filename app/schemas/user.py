from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from .common import Password, OptionalEmail, RegionName


class UserInfo(BaseModel):
    cuid: str
    name: str
    email: EmailStr
    region_id: int | None = Field(description="사용자의 동네 ID 기본값")
    region_name: RegionName | None = Field(description="동네 ID에 해당하는 동네 이름")


class UserInfoUpdateRequest(BaseModel):
    name: str | None = None
    email: OptionalEmail = None
    region_id: int | None = Field(None, description="동네 ID. null로 설정할 경우 동네 설정이 해제됨")

class UserPasswordChangeRequest(BaseModel):
    current_password: str
    new_password: Password
