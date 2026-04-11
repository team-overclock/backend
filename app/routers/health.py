"""헬스 체크 엔드포인트 라우트 모듈."""

from fastapi import APIRouter

from ..schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/", status_code=200)
def hello_world() -> HealthResponse:
    """서비스 기본 응답 반환."""
    return {"Hello": "World"}
