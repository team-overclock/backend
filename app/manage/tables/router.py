"""관리용 라우터"""

from fastapi import APIRouter, status

from ..schemas import ImmediateResponse

from .create import run as create
from .drop import run as drop


router = APIRouter(prefix="/tables")


@router.post(
    "",
    summary="테이블 생성",
    status_code=status.HTTP_201_CREATED,
)
def create_table(
) -> ImmediateResponse:
    """모든 테이블 생성"""

    try:
        create()
        success = True
    except:
        success = False
    
    return {
        "success": success,
    }

@router.delete(
    "",
    summary="테이블 삭제",
    status_code=status.HTTP_200_OK,
)
def drop_table(
) -> ImmediateResponse:
    """모든 테이블 삭제"""

    try:
        drop()
        success = True
    except:
        success = False
    
    return {
        "success": success,
    }
