import os
import sys
import re
import shutil
import gdown
from time import time
from pathlib import Path

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils import read_file, write_file


TIMESTAMP = round(time())
SCRATCH_TIMESTAMP_FILENAME = ".timestamp"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BACKUP_DIR = DATA_DIR / ".backup"
DOWNLOADING_DIR = DATA_DIR / ".downloading"
VERSION_FILE = str(DATA_DIR / "version.txt")
VERSION_TEMP_FILE = str(DATA_DIR / ".version.tmp")
URL_FILE = str(DATA_DIR / "url.txt")


def usage():
    print("사용법: python download_data.py")
    print("  - 현재 다운로드된 데이터의 버전을 확인하고 구글 드라이브에서 데이터를 다운로드합니다.")
    print("  - 다운로드된 파일은 data 폴더에 위치합니다.")


def make_scratch_folder():
    file = DOWNLOADING_DIR / "scratch" / SCRATCH_TIMESTAMP_FILENAME
    if file.exists():
        ts = int(read_file(str(file), strip=True))
        if TIMESTAMP - ts < 60 * 60 * 24:
            return file.parent

    shutil.rmtree(str(file.parent), ignore_errors=True)
    file.parent.mkdir(parents=True, exist_ok=True)
    write_file(str(file), str(TIMESTAMP))
    return file.parent


def read_url_file(filepath: str) -> dict[str, str]:
    urls = {}
    content = read_file(filepath)
    if not content: return urls

    for line in content.splitlines():
        line = re.sub(r"#.*", "", line).strip()
        if not line: continue

        idx = line.find(":")
        if idx == -1: continue

        key = line[:idx].strip()
        value = line[idx+1:].strip()
        if value: urls[key] = value
    return urls


def download_file(*, silent: bool = False, **kwargs):
    return gdown.download(
        **kwargs,
        quiet=silent,
        resume=True,
    )

def download_folder(*, silent: bool = False, **kwargs):
    return gdown.download_folder(
        **kwargs,
        quiet=silent,
        resume=True,
    )


def move_folder(source: str, dest: str, *, ignore: list[str] = [], silent: bool = False):
    src = Path(source)
    dst = Path(dest)
    dst.mkdir(parents=True, exist_ok=True)

    for path in src.iterdir():
        if path == dst or path.name in ignore:
            continue
        try:
            target_path = dst / path.name
            shutil.move(str(path), str(target_path))
        except Exception as e:
            if not silent: print(f"Move Failed: {e}")

    if not list(src.iterdir()):
        os.rmdir(str(src))



def run(*, silent: bool = False):
    P = not silent

    urls = read_url_file(URL_FILE)

    if P: print("현재 버전 확인 중...")
    curr_version = read_file(VERSION_FILE, strip=True)
    if P: print(f"현재 버전: {curr_version or 'No Version'}")

    if not curr_version:
        if P: print("버전 파일이 없습니다. 데이터를 다운로드합니다.")
        output_folder = str(make_scratch_folder())
    else:
        if P: print("최신 버전 확인 중...")
        download_file(url=urls["version"], output=VERSION_TEMP_FILE, silent=True)

        new_version: str = read_file(VERSION_TEMP_FILE, strip=True)
        if curr_version == new_version:
            if P: print(f"현재 최신 버전입니다.")
            return False
        if P: print(f"최신 버전({new_version})을 다운로드합니다.")
        output_folder = str(DOWNLOADING_DIR / new_version)

    download_folder(url=urls["google drive"], output=output_folder, silent=silent)

    if curr_version:
        move_folder(
            str(DATA_DIR),
            str(BACKUP_DIR / curr_version),
            ignore=[
                Path(VERSION_TEMP_FILE).name,
                BACKUP_DIR.name,
                DOWNLOADING_DIR.name,
            ],
            silent=silent,
        )
    move_folder(output_folder, str(DATA_DIR))
    if curr_version:
        os.remove(VERSION_TEMP_FILE)
    else:
        os.remove(str(DATA_DIR / SCRATCH_TIMESTAMP_FILENAME))

    return True


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) != 1:
        usage()
        sys.exit(1)

    run()
