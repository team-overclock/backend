from fastapi import Request

from .core.exception import AppException


def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        # 프론트엔드가 이 401 에러를 받으면 "로그인 후 사용 가능" 팝업을 띄웁니다.
        raise AppException(status_code=401, message="로그인이 필요한 서비스입니다.")
    return session_id