from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.auth import UserCreate, UserLogin # UserLogin 스키마 필요
from ..core.security import verify_password     # 보안 로직 불러오기
from ..core.exception import AppException
from ..crud.user import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])

# --- 회원가입 ---
@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # 이미 가입된 이메일인지 체크하는 로직을 crud에 추가하는 것이 좋습니다.
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise AppException(status_code=400, message="이미 등록된 이메일입니다.")
    
    new_user = create_user(db=db, user=user)
    return {"message": "회원가입 성공", "user": new_user.name}

# --- 로그인 (세션 발급) ---
@router.post("/login")
def login(login_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    # 1. DB에서 해당 이메일 유저 찾기
    user = get_user_by_email(db, email=login_data.email)
    if not user:
        raise AppException(status_code=400, message="이메일 또는 비밀번호가 잘못되었습니다.")

    # 2. 비밀번호 검증 (security.py의 함수 사용)
    if not verify_password(user.password, login_data.password):
        raise AppException(status_code=400, message="이메일 또는 비밀번호가 잘못되었습니다.")

    # 3. 세션 쿠키 설정 (보안 전공자의 디테일)
    # 실제 운영 시에는 유저 ID 대신 암호화된 토큰이나 UUID를 사용합니다.
    response.set_cookie(
        key="session_id", 
        value=str(user.seq), 
        httponly=True,   # JS에서 쿠키 접근 차단 (XSS 방어)
        samesite="lax",  # CSRF 방어
        secure=False     # 배포(HTTPS) 시에는 True로 변경 필수!
    )
    return {"message": "로그인 성공", "user_name": user.name}

# --- 로그아웃 (세션 삭제) ---
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("session_id")
    return {"message": "로그아웃 성공"}