import os
import re
import shutil
import gdown
from pathlib import Path

from ...utils import read_file, write_file
from ...config import (
    DATA_DIR,
    DATA_BACKUP_DIR,
    DATA_DOWNLOADING_DIR,
    DATA_DOWNLOADING_VERSION_FILE,
    DATA_VERSION_FILE,
    DATA_VERSION_TEMP_FILE,
    DATA_URL_FILE,
)



def get_current_version():
    return read_file(DATA_VERSION_FILE, strip=True)


def get_downloading_version():
    return read_file(DATA_DOWNLOADING_VERSION_FILE, strip=True)

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



def run(*, silent: bool = False) -> bool:
    """
    데이터 디렉터리에 버전 정보를 확인하여 최신 버전이 아니면 다운로드하여 교체합니다.
    
    Returns:
        bool: 데이터가 업데이트되었는지 여부
    """

    P = not silent

    urls = read_url_file(DATA_URL_FILE)

    if P: print("현재 버전 확인 중...")
    curr_version = read_file(DATA_VERSION_FILE, strip=True)
    if P: print(f"현재 버전: {curr_version or 'No Version'}")

    if P: print("최신 버전 확인 중...")
    download_file(url=urls["version"], output=DATA_VERSION_TEMP_FILE, silent=True)
    new_version: str = read_file(DATA_VERSION_TEMP_FILE, strip=True)
    if curr_version:
        if curr_version == new_version:
            if P: print(f"현재 최신 버전입니다.")
            return False
        if P: print(f"최신 버전({new_version})을 다운로드합니다.")
        output_folder = str(DATA_DOWNLOADING_DIR / new_version)

    try:
        write_file(str(DATA_DOWNLOADING_VERSION_FILE), new_version)
        download_folder(url=urls["google drive"], output=output_folder, silent=silent)
    finally:
        os.remove(DATA_DOWNLOADING_VERSION_FILE)

    if curr_version:
        move_folder(
            str(DATA_DIR),
            str(DATA_BACKUP_DIR / curr_version),
            ignore=[
                Path(DATA_VERSION_TEMP_FILE).name,
                DATA_BACKUP_DIR.name,
                DATA_DOWNLOADING_DIR.name,
            ],
            silent=silent,
        )
    move_folder(output_folder, str(DATA_DIR))
    os.remove(DATA_VERSION_TEMP_FILE)

    return True
