from fastapi import Request

from ..models import User
from ..schemas.auth import UserSession


def login(request: Request, user: User):
    request.session["user_cuid"] = user.cuid

def logout(request: Request):
    request.session.clear()


def get_session(request: Request):
    user_cuid = request.session.get("user_cuid")
    return UserSession(cuid=user_cuid) if user_cuid else None
