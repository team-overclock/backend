from fastapi import Request, status

from .core.exception import AppException
from .core.session import get_session


def get_current_user(request: Request):
    session = get_session(request)
    if not session:
        # 세션이 없으면 401 에러를 발생시킴
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="로그인이 필요한 서비스입니다.",
        )
    return session
