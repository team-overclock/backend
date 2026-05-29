#!/usr/bin/with-contenv python3

import os
import sys

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from app.config import DEFAULT_INSERT_SEED_RECOMMENDATIONS, DEFAULT_INSERT_SEED_USERS


def usage():
    print(f"사용법: python insert_seeds.py [생성할 추천 수] [생성할 사용자 수]")
    print(f"  - 데이터베이스 내 데이터를 기반으로 랜덤 추천 데이터를 생성하여 삽입합니다.")
    print(f"  - 생성할 추천 수 기본 값: {DEFAULT_INSERT_SEED_RECOMMENDATIONS}")
    print(f"  - 생성할 사용자 수 기본 값: {DEFAULT_INSERT_SEED_USERS}")
    print(f"  - 유저를 먼저 생성한 후 추천 데이터를 생성합니다.")


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) > 3:
        usage()
        sys.exit(1)

    try:
        args = [int(arg) for arg in sys.argv[1:]]
    except:
        usage()
        sys.exit(1)

    from app.manage import seeds
    try:
        seeds.insert(*args)
    except Exception as e:
        print("시드 데이터 삽입 중 오류가 발생했습니다.")
        raise e
    else:
        print("모든 시드 데이터가 삽입되었습니다.")
