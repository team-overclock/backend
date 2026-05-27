import os


MODE = os.getenv("APP_ENV") or "development"
"""애플리케이션 실행 모드"""

PROD = MODE == "production"
"""운영 모드 여부"""
