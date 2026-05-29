#!/usr/bin/with-contenv python3

import os
import sys

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def usage():
    print("사용법: python insert_data.py")
    print("  - data 폴더 내 *.csv 파일 데이터를 데이터베이스에 삽입합니다.")


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) > 2:
        usage()
        sys.exit(1)

    from app.manage import data
    data.insert()
