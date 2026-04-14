from sqlalchemy.orm import Session

from .models import User, Region, InfrastructureType
from .schemas.auth import UserCreate
from .core.security import hash_password


def get_regions_by_depth(db: Session, depth: int = 2):
    """주어진 depth에 해당하는 동네 목록을 반환하는 함수"""
    return db.query(Region).filter(Region.depth == depth).all()

def get_region_by_id(db: Session, region_id: int, depth: int = 2):
    """주어진 id에 해당하는 동네를 반환하는 함수"""
    return db.query(Region).filter(Region.id == region_id, Region.depth == depth).first()

def get_all_infrastructure_types(db: Session):
    """인프라 유형 목록을 반환하는 함수"""
    return db.query(InfrastructureType).all()

def get_infrastructure_by_id(db: Session, infrastructure_id: int):
    """주어진 id에 해당하는 인프라를 반환하는 함수"""
    return db.query(InfrastructureType).filter(InfrastructureType.id == infrastructure_id).first()


def create_user(db: Session, user: UserCreate):
    # 비밀번호 암호화! (보안 전공자의 자존심)
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

# src/app/crud.py 에 추가
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.e_mail == email).first()