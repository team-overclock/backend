from fastapi import Request, Depends, status
from sqlalchemy.orm import Session

from .core.exception import AppException
from .core.session import get_session
from .core.validate import verify_recommendation
from .database import get_db
from .schemas.auth import UserSession
from .crud.user import get_user_by_id
from .crud.service import get_user_recommendations_by_user_id


def get_current_user(request: Request):
    session = get_session(request)
    if not session:
        # 세션이 없으면 401 에러를 발생시킴
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="로그인이 필요한 서비스입니다.",
        )
    return session

def only_self_access(
    request: Request,
    session: UserSession = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    `/users/me`, `/users/{user_id}` 엔드포인트 등에서 `user_id`가 본인 ID와 일치하는 경우에만 접근을 허용하는 의존성 함수.
    `user_id`가 본인 ID와 다르면 404 에러를 발생시킴
    - `{user_id}`가 포함된 경로는 해당 값을 기준으로 검증
    - `/users/me`와 같은 `{user_id}`가 없는 경로에 사용 시에는 세션의 사용자 ID로 검증
    """
    user_id = request.path_params.get("user_id", session.id)
    user = get_user_by_id(db, user_id) if session.id == user_id else None
    if not user:
        # user_id가 세션의 사용자 ID와 다르면 403 에러를 발생시킴
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="접근 권한이 없습니다.",
        )
    return user

def get_current_recommendation(
    task_id: str,
    session: UserSession = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    `/recommendations/{task_id}` 엔드포인트에서 `task_id`에 해당하는 추천이 현재 세션의 사용자에게 속한 것인지 검증하는 의존성 함수.
    `task_id`에 해당하는 추천이 존재하지 않거나, 존재하지만 현재 세션의 사용자에게 속하지 않으면 400 에러를 발생시킴
    """
    return verify_recommendation(db, task_id, session.id)

def get_current_user_recommendations(
    session: UserSession = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    현재 로그인된 사용자가 요청한 추천 목록을 반환하는 의존성 함수.
    """
    return get_user_recommendations_by_user_id(db, session.id)
