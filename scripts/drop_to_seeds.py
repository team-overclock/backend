#!/usr/bin/with-contenv python3

import os
import sys
import time

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))



def usage():
    print("사용법: python drop_to_seeds.py [생성할 추천 수] [생성할 사용자 수]")
    print("  - drop_tables.py, insert_data.py, insert_seeds.py를 순차적으로 실행합니다.")


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) > 3:
        usage()
        sys.exit(1)

    print("!!! 3초 후 모든 데이터를 삭제하고 다시 생성합니다 !!!")
    print("중단하려면 Ctrl+C를 누르세요.")
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print("\n작업이 중단되었습니다.")
        sys.exit(0)

    try:
        args = [int(arg) for arg in sys.argv[1:]]
    except:
        usage()
        sys.exit(1)

    from scripts import drop_tables, insert_data
    from app.manage import seeds
    try:
        drop_tables.main(force=True)
        insert_data.main()
        seeds.insert(*args)
    except Exception as e:
        print("작업 중 오류가 발생했습니다.")
        raise e
    else:
        print("작업이 완료되었습니다.")
