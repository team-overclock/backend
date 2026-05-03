from sqlalchemy.orm import Session

from .models import User, Region, InfrastructureType
from .models.region import Region
from .schemas.auth import UserCreate
from .core.security import hash_password


def get_regions_by_depth(db: Session, depth: int = 2):
    """주어진 depth에 해당하는 동네들의 id와 full_name을 반환하는 함수"""
    regions = db.query(Region).filter(Region.depth == depth).all()
    region_map: dict[str, int] = {}
    region_names: list[str] = []
    for r in regions:
        region_map[r.full_name] = r.id
        region_names.append(r.full_name)
    return region_map, region_names

def get_regions_by_full_name(db: Session, full_name: str, depth: int = 2):
    """주어진 full_name에 해당하는 동네의 id를 반환하는 함수"""
    region = db.query(Region).filter(Region.depth == depth, Region.full_name == full_name).first()
    return region

def get_all_infrastructure_types(db: Session) -> list[str]:
    """인프라 유형 목록을 반환하는 함수"""
    infrastructure_types = db.query(InfrastructureType).all()
    return [item.name for item in infrastructure_types]


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