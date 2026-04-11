from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    e_mail: EmailStr  # DB 필드명과 일치시킴
    password: str

class UserCreate(BaseModel):
    name: str
    e_mail: EmailStr
    password: str
    region: str