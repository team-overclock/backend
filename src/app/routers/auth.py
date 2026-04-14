from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.auth import UserCreate
from ..core.security import hash_password

def create_user(db: Session, user: UserCreate):
    # 비밀번호 암호화
    hashed_pwd = hash_password(user.password)
    
    db_user = User(
        name=user.name,
        e_mail=user.e_mail,
        passwd=hashed_pwd, # 암호화된 비밀번호 저장
        region=user.region
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user