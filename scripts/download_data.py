import os
import sys
import re
import shutil
import gdown
from time import time
from pathlib import Path

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def usage():
    print("사용법: python download_data.py")
    print("  - 현재 다운로드된 데이터의 버전을 확인하고 구글 드라이브에서 데이터를 다운로드합니다.")
    print("  - 다운로드된 파일은 data 폴더에 위치합니다.")



if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) != 1:
        usage()
        sys.exit(1)

    from app.manage import data
    data.download()
