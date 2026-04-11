"""Scalar API 문서 페이지 라우트 모듈."""

from fastapi import APIRouter, Request
from scalar_fastapi import AgentScalarConfig, Theme, get_scalar_api_reference

router = APIRouter()


@router.get("")
async def scalar_html(request: Request):
    """Scalar 문서 HTML 응답 생성 및 반환."""
    return get_scalar_api_reference(
        openapi_url=request.app.openapi_url,
        theme=Theme.NONE,
        agent=AgentScalarConfig(disabled=True),
        overrides={
            # https://scalar.com/products/api-references/configuration
            "persistAuth": True,
            "defaultOpenFirstTag": False,
        },
    )
