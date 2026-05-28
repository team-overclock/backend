import re
from os import linesep
from pathlib import Path
from typing import TypeVar, Generator, Callable, Iterable, Literal


SEED_TASK_ID_PREFIX = "random_seed_"
SEED_USERNAME_PREFIX = "seed_user_"


T = TypeVar("T")
R = TypeVar("R")


def sniff_encoding(path: str) -> str:
    """
    파일의 인코딩을 추측하여 반환합니다.

    Args:
        path (str): 파일 경로

    Returns:
        str: "utf-8" 또는 "cp949"
    """

    try:
        with open(path, encoding="utf-8") as f:
            f.readline()
        return "utf-8"
    except Exception:
        return "cp949"


def get_files(
    directory_path: str,
    *,
    extensions: list[str] | str | None = None,
    recursive: bool = False
) -> Generator[str, None, None]:
    """
    지정된 디렉토리에서 특정 확장자를 가진 파일들의 경로를 반환합니다.

    Args:
        directory_path (str): 검색할 디렉토리 경로
        extensions (list[str] | str | None): 검색할 파일 확장자 목록 (예: [".csv", ".shp"]). None이면 모든 파일을 반환합니다.
        recursive (bool): 하위 디렉토리까지 검색할지 여부 (기본값: False)

    Returns:
        Generator[str, None, None]: 지정된 확장자를 가진 파일들의 경로 제너레이터
    """

    extensions = extensions or [""]
    if isinstance(extensions, str):
        extensions = [extensions]

    for ext in extensions:
        paths = Path(directory_path).rglob(f"*{ext}")
        for path in paths:
            if path.is_file():
                yield str(path)
            elif path.is_dir() and recursive:
                yield from get_files(str(path), extensions=extensions, recursive=recursive)


def read_file(file_path: str, *, strip: bool = False) -> str | None:
    try:
        enc = sniff_encoding(file_path)
        with open(file_path, encoding=enc) as f:
            content = f.read()
            if strip: content = content.strip()
            return content
    except:
        pass

def write_file(file_path: str, content: str, *, encoding: str | None = None, append: bool = False) -> None:
    if not encoding and Path(file_path).exists():
        encoding = sniff_encoding(file_path)
    elif not encoding:
        encoding = "utf-8"

    with open(file_path, mode="a" if append else "w", encoding=encoding) as f:
        f.write(content)


def progress(
    msg: str,
    current: int,
    *,
    total: int | None = None,
    is_final: bool | None = None,
    eol: Literal["\n", "\r\n"] = linesep,
    silent: bool = False,
    unit: str = "items",
    unit_always: bool = False,
    percentage: bool = True,
) -> None:
    """
    한 줄을 지우고 진행률을 출력합니다. 마지막이면 개행합니다.

    - `\\x1b[K`로 커서 위치부터 라인 끝까지 지워 남은 글자 문제를 해결합니다.
    """

    if not silent:
        is_final = current == total if is_final is None else is_final
        end = eol if is_final else ""

        prefix = msg
        status = current if total is None else f"{current}/{total}"
        suffix = unit if total is None or unit_always else ""
        suffix += f" {current/total*100:.2f}%" if percentage and total is not None else ""

        print(f"\r  {prefix} {status} {suffix}\x1b[K", end=end, flush=True)


def parse_int(value: str | None) -> int | None:
    """
    `90,300` 같은 문자열을 int로 변환합니다.
    """

    if value is None:
        return None

    s = str(value).strip().replace(",", "")
    if s in {"", "-"}:
        return None
    if not re.fullmatch(r"\d+", s):
        return None
    return int(s)


def parse_float(value: str | None) -> float | None:
    """
    `123.45` 같은 문자열을 float로 변환합니다.
    """

    if value is None:
        return None

    s = str(value).strip()
    if s in {"", "-"}:
        return None

    try:
        return float(s)
    except Exception:
        return None


def run_with_progress(
    items: Iterable[T],
    msg: str,
    callback: Callable[[int, T], R],
    *,
    total: int | None = None,
    interval: int = 1,
    eol: Literal["\n", "\r\n"] = linesep,
    silent: bool = False,
) -> list[R]:
    """
    작업을 수행하면서 진행 상황을 터미널에 출력합니다.

    :param items: 작업할 아이템들의 iterable (예: 리스트, 제너레이터 등)
    :param msg: 진행률 앞에 표시될 메시지
    :param callback: 각 루프에서 실행할 함수 (인자로 현재 인덱스 및 아이템 전달)
    :param total: 총 반복 횟수, items이 시퀀스인 경우 자동 탐지
    :param interval: 진행률을 갱신할 주기 (기본값: 1)
    :param eol: 작업 완료 후 개행 문자
    :param silent: True로 설정하면 진행률 출력 없이 조용히 실행
    """

    results = []
    if silent:
        for idx, item in enumerate(items):
            results.append(callback(idx, item))
    else:
        has_len = hasattr(items, "__len__")
        if has_len and total is None:
            total = len(items)

        idx = -1
        for idx, item in enumerate(items):
            if idx == 0 or idx % interval == 0:
                progress(msg, idx, total=total)
            results.append(callback(idx, item))
        progress(msg, idx + 1, total=total, is_final=True, eol=eol)
    return results
