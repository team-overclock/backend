#!/usr/bin/with-contenv python3

import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def usage():
    print("사용법: python drop_tables.py [-y|--yes]")
    print("  - 모든 데이터베이스 테이블을 삭제합니다.")


def main():
    try:
        from app.manage import tables
        tables.drop()
    except Exception as e:
        print("데이터베이스 테이블 삭제 중 오류가 발생했습니다.")
        raise e
    else:
        print("모든 데이터베이스 테이블이 삭제되었습니다.")


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) > 2:
        usage()
        sys.exit(1)
    elif len(sys.argv) != 2 or sys.argv[1] not in ("-y", "--yes"):
        print("⚠️  경고: 모든 데이터베이스 테이블이 삭제됩니다.")
        confirm = input("정말로 진행하시겠습니까? (y/N): ").lower()
        if confirm not in ("y", "yes"):
            print("작업이 취소되었습니다.")
            sys.exit(0)

    main()
