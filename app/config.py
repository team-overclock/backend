import os


def parse_comma_separated(key: str, default_value: str):
	value = os.getenv(key) or default_value
	items = [x.strip() for x in value.split(",") if x.strip()]
	return items


MODE = os.getenv("APP_ENV") or "development"
"""애플리케이션 실행 모드"""

PROD = MODE == "production"
"""운영 모드 여부"""


ALLOWED_HOSTS = parse_comma_separated("ALLOWED_HOSTS", "localhost")
"""허용된 호스트 목록 (도메인)"""

TRUSTED_HOSTS = parse_comma_separated("TRUSTED_HOSTS", "127.0.0.1")
"""신뢰할 수 있는 프록시 IP 목록"""
