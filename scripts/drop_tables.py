import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.database import engine
from app.models import Base


def usage():
    print("사용법: python drop-tables.py [-y|--yes]")

def main(*, force: bool | None = None):
    if force is None:
        print("⚠️  경고: 모든 데이터베이스 테이블이 삭제됩니다.")
        confirm = input("정말로 진행하시겠습니까? (y/N): ").lower()
        force = confirm in ("y", "yes")

    if force:
        Base.metadata.drop_all(bind=engine)
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
