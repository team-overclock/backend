import os
from pathlib import Path


def parse_comma_separated(key: str, default_value: str):
    value = os.getenv(key) or default_value
    items = [x.strip() for x in value.split(",") if x.strip()]
    return items


MODE = os.getenv("MODE") or "development"
"""애플리케이션 실행 모드"""

PROD = MODE == "production"
"""운영 모드 여부"""


ALLOWED_HOSTS = parse_comma_separated("ALLOWED_HOSTS", "localhost")
"""허용된 호스트 목록 (도메인)"""

TRUSTED_HOSTS = parse_comma_separated("TRUSTED_HOSTS", "127.0.0.1")
"""신뢰할 수 있는 프록시 IP 목록"""


GUEST_LOGIN_ENABLE = (os.getenv("GUEST_LOGIN_ENABLE") or "").lower() == "true"

SEED_TASK_ID_PREFIX = "random_seed_"
SEED_USERNAME_PREFIX = "seed_user_"

DEFAULT_INSERT_SEED_RECOMMENDATIONS = 30
DEFAULT_INSERT_SEED_USERS = 0



DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_BACKUP_DIR = DATA_DIR / ".backup"
DATA_DOWNLOADING_DIR = DATA_DIR / ".downloading"
DATA_DOWNLOADING_VERSION_FILE = DATA_DOWNLOADING_DIR / ".version"
DATA_VERSION_FILE = str(DATA_DIR / "version.txt")
DATA_VERSION_TEMP_FILE = str(DATA_DIR / ".version.tmp")
DATA_URL_FILE = str(DATA_DIR / "url.txt")
