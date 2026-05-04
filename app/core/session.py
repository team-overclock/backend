from fastapi import Request

from ..models import User
from ..schemas.auth import UserSession


def login(request: Request, user: User):
    request.session["user_id"] = user.id

def logout(request: Request):
    request.session.clear()


def get_session(request: Request):
    user_id = request.session.get("user_id")
    return UserSession(id=user_id) if user_id else None
