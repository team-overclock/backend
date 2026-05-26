from fastapi import Request, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from .core.enums import AppErrorCodeEnum
from .core.exception import AppException
from .core.session import get_session
from .database import get_db
from .models import User
from .schemas.auth import UserSession
from .crud.user import get_user_by_cuid
from .crud.service import (
    get_recommendations_by_user_id_and_task_id,
    get_search_log_by_user_id_and_task_id,
    get_search_log_by_user_id,
)


def get_current_user_session(request: Request):
    session = get_session(request)
    if not session:
        # 세션이 없으면 401 에러를 발생시킴
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=AppErrorCodeEnum.AUTHENTICATION_REQUIRED,
            message="로그인이 필요한 서비스입니다.",
        )
    return session

def only_self_access(
    request: Request,
    session: UserSession = Depends(get_current_user_session),
    db: Session = Depends(get_db),
):
    """
    `{user_cuid}` 또는 세션으로 사용자를 검증하는 의존성 함수.
    - `user_cuid`가 포함된 경로는 세션에 저장된 cuid와 비교 검증 및 DB에 해당 사용자가 존재하는지 검증
    - `user_cuid`가 없는 경로는 세션에 저장된 cuid를 가진 사용자가 DB에 존재하는지 검증
    - 검증 실패 시 403 에러를 발생시킴
    """
    user_cuid = request.path_params.get("user_cuid", session.cuid)
    user = get_user_by_cuid(db, user_cuid) if session.cuid == user_cuid else None
    if not user:
        # user_cuid가 세션의 사용자 CUID와 다르면 403 에러를 발생시킴
        # {user_cuid}가 아닌 세션 기반인 경우에는 세션 cuid가 DB에 존재하지 않는 경우임
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=AppErrorCodeEnum.FORBIDDEN,
            message="접근 권한이 없습니다.",
        )
    return user

def _get_current_rec_or_search_log(
    task_id: str,
    db: Session,
    user: User,
    fn: callable,
):
    task_id = task_id if len(task_id) >= 8 else None
    items = fn(db, user.id, task_id, size=2) if task_id else []

    ins = None
    if len(items) == 1:
        ins = items[0]
    elif task_id and len(items) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )
    else:  # not task_id or len(items) > 1
        for item in items:
            if item.task_id == task_id:
                ins = item
                break
        if ins is None:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code=AppErrorCodeEnum.TASK_ID_TOO_SHORT,
                message="task_id 값이 너무 짧습니다.",
            )
    return ins

def get_current_recommendation(
    task_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(only_self_access),
):
    """
    `task_id` 값으로 시작하는 추천이 현재 세션의 사용자에게 속한 것인지 검증하는 의존성 함수.
    - task_id가 없거나 너무 짧거나 추천이 2개 이상 조회되면 400 에러를 발생시킴
    - 추천이 존재하지 않으면 404 에러를 발생시킴
    """

    return _get_current_rec_or_search_log(task_id, db, user, get_recommendations_by_user_id_and_task_id)

def get_current_search_log(
    task_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(only_self_access),
):
    """
    `task_id` 값으로 시작하는 검색 기록이 현재 세션의 사용자에게 속한 것인지 검증하는 의존성 함수.
    - task_id가 없거나 너무 짧거나 검색 기록이 2개 이상 조회되면 400 에러를 발생시킴
    - 검색 기록이 존재하지 않으면 404 에러를 발생시킴
    """

    return _get_current_rec_or_search_log(task_id, db, user, get_search_log_by_user_id_and_task_id)


def get_current_user_recommendations(
    db: Session = Depends(get_db),
    user: User = Depends(only_self_access),
):
    """
    현재 로그인된 사용자가 요청한 추천 목록을 반환하는 의존성 함수.
    """
    return get_search_log_by_user_id(db, user.id)
