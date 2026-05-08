from sqlalchemy.orm import Session

from ..models.user import User
from ..schemas.auth import UserCreate
from ..core.security import hash_password


def create_user(db: Session, user: UserCreate):
    # 비밀번호 암호화! (보안 전공자의 자존심)
    hashed_pwd = hash_password(user.password)
    
    db_user = User(
        name=user.name,
        email=user.email,
        password=hashed_pwd, # 암호화된 비밀번호 저장
        region=user.region
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# src/app/crud.py 에 추가
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()
