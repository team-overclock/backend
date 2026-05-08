from sqlalchemy.orm import Session

from ..models import Region, InfrastructureType


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
