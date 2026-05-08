from sqlalchemy.orm import Session

from ..models import User, Region, InfrastructureType, Recommendation, UserRecommendation


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

def get_infrastructure_by_ids(db: Session, infrastructure_ids: list[int]):
    """주어진 id에 해당하는 인프라를 반환하는 함수"""
    return db.query(InfrastructureType).filter(InfrastructureType.id.in_(infrastructure_ids)).all()


def get_recommendation_by_hash(db: Session, recommendation_hash: str):
    """주어진 hash에 해당하는 추천을 반환하는 함수"""
    return db.query(Recommendation).filter(Recommendation.hash == recommendation_hash).first()

def get_recommendation_by_hash_and_user_id(db: Session, recommendation_hash: str, user_id: str):
    """주어진 hash와 user_id에 해당하는 추천을 반환하는 함수"""
    return db.query(Recommendation).join(
        UserRecommendation,
        Recommendation.id == UserRecommendation.recommendation_id,
    ).filter(
        UserRecommendation.user_id == user_id,
        Recommendation.hash == recommendation_hash,
    ).first()

def get_user_recommendations_by_user_id(db: Session, user_id: str):
    """주어진 user_id가 요청한 추천 목록을 반환하는 함수"""
    return db.query(UserRecommendation).join(
        User,
        UserRecommendation.user_id == User.id,
    ).join(
        Recommendation,
        UserRecommendation.recommendation_id == Recommendation.id,
    ).filter(
        UserRecommendation.user_id == user_id,
    ).all()
