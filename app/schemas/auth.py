from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    email: EmailStr  # DB 필드명과 일치시킴
    password: str

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    region: str