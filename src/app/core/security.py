from passlib.context import CryptContext

# Bcrypt 알고리즘 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """평문 비밀번호를 해시값으로 변환"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """입력된 비밀번호와 DB의 해시값 비교"""
    return pwd_context.verify(plain_password, hashed_password)