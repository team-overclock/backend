from sqlalchemy.orm import Session

from ..core.validate import verify_region
from ..models.user import User
from ..schemas.auth import UserCreateRequest


def create_user(db: Session, user: UserCreateRequest):
    """이메일 중복 체크 후 사용자 생성"""
    created = False
    db_user = get_user_by_email(db, user.email)
    if not db_user:
        created = True
        region = verify_region(db, user.region_id, 2)

        # 비밀번호 암호화는 User 클래스에서 자동으로 처리되도록 함
        db_user = User(
            name=user.name,
            email=user.email,
            password=user.password,
            region=region,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    return db_user, created

def get_user_by_id(db: Session, user_id: int):
    """ID로 사용자 조회, 없으면 None 반환"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_cuid(db: Session, user_cuid: str):
    """CUID로 사용자 조회, 없으면 None 반환"""
    return db.query(User).filter(User.cuid == user_cuid).first()

def get_user_by_email(db: Session, email: str):
    """이메일로 사용자 조회, 없으면 None 반환"""
    return db.query(User).filter(User.email == email).first()
