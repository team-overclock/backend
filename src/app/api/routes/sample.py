"""예시 엔드포인트 라우트 모듈."""

from fastapi import APIRouter

router = APIRouter(prefix="/prefix/path", tags=["tag1", "tag2"], redirect_slashes=False)


@router.get("", tags=["tag3"])
def hello_router() -> dict[str, str]:
    """샘플 JSON 응답 반환."""
    return {"Hello": "Router"}
