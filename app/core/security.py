from argon2 import PasswordHasher

# argon2 알고리즘 설정
pwd_context = PasswordHasher()

def hash_password(password: str) -> str:
    """평문 비밀번호를 해시값으로 변환"""
    return pwd_context.hash(password)

def verify_password(hashed_password: str, plain_password: str) -> bool:
    """입력된 비밀번호와 DB의 해시값 비교"""
    try:
        return pwd_context.verify(hashed_password, plain_password)
    except:
        return False
