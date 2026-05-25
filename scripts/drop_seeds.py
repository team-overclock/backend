#!/usr/bin/with-contenv python3

import os
import sys

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def usage():
    print("사용법: python drop-seeds.py [-y|--yes]")
    print("  - 모든 데이터베이스 테이블을 삭제합니다.")


def main(*, force: bool = False):
    if force is True:
        drop = True
    else:
        print("⚠️  경고: 모든 데이터베이스 테이블이 삭제됩니다.")
        confirm = input("정말로 진행하시겠습니까? (y/N): ").lower()
        drop = confirm in ("y", "yes")

    if drop:
        from app.database import SessionLocal
        from app.models import User, Recommendation
        from scripts.common import SEED_TASK_ID_PREFIX, SEED_USERNAME_PREFIX

        db = SessionLocal()
        db.query(User).filter(User.name.like(f"{SEED_USERNAME_PREFIX}%")).delete()
        db.query(Recommendation).filter(Recommendation.task_id.like(f"{SEED_TASK_ID_PREFIX}%")).delete()
        db.commit()
        db.close()
        print("모든 테이블이 삭제되었습니다.")
    else:
        print("작업이 취소되었습니다.")


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) > 2:
        usage()
        sys.exit(1)
    elif len(sys.argv) == 2 and sys.argv[1] in ("-y", "--yes"):
        main(force=True)
    else:
        main()
