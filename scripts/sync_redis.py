#!/usr/bin/with-contenv python3

import os
import sys

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def usage():
    print("사용법: python sync_redis.py")
    print("  - 데이터베이스의 지역 및 고등학교 데이터를 Redis에 동기화합니다.")


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) > 1:
        usage()
        sys.exit(1)

    from app.manage import data
    data.sync_redis()
