#!/usr/bin/with-contenv python3

import os
import sys

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def usage():
    print("사용법: python insert_scores.py")
    print("  - DB 내 삽입된 Property와 Infrastructure 데이터를 기반으로 RADIUS_METERS 미터 이내의 모든 연관 관계(거리, 도보시간, 원천점수)를 계산하여 다대다 중간 매핑 테이블에 삽입합니다.")


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) > 2:
        usage()
        sys.exit(1)

    from app.manage import scores
    scores.insert()
