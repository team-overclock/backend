"""헬스 체크 엔드포인트 라우트 모듈."""

from fastapi import APIRouter, status

from ..schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/",
    summary="헬스 체크",
    status_code=status.HTTP_200_OK,
)
def hello_world() -> HealthResponse:
    """서비스 기본 응답 반환."""
    return {"Hello": "World"}
