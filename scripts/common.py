import re
from os import linesep
from typing import Callable, Literal
from decimal import Decimal


def progress(msg: str, current: int, total: int, *, is_final: bool | None = None, eol: Literal["\n", "\r\n"] = linesep) -> None:
    """한 줄을 지우고 진행률을 출력합니다. 마지막이면 개행합니다.

    - `\\x1b[K`로 커서 위치부터 라인 끝까지 지워 남은 글자 문제를 해결합니다.
    """

    is_final = current == total if is_final is None else is_final
    end = eol if is_final else ""
    print(f"\r  {msg} {current}/{total}\x1b[K", end=end, flush=True)


def parse_price_to_int(value: str | None) -> int | None:
    """`90,300` 같은 문자열을 int로 변환합니다."""

    if value is None:
        return None

    s = str(value).strip().replace(",", "")
    if s in {"", "-"}:
        return None
    if not re.fullmatch(r"\d+", s):
        return None
    return int(s)


def parse_decimal(value: str | None) -> Decimal | None:
    """`123.45` 같은 문자열을 Decimal로 변환합니다."""

    if value is None:
        return None

    s = str(value).strip()
    if s in {"", "-"}:
        return None

    try:
        return Decimal(s)
    except Exception:
        return None


def run_with_progress(
    msg: str,
    total_count: int,
    callback: Callable[[int], None],
    *,
    interval: int = 1,
    eol: Literal["\n", "\r\n"] = linesep
):
    """
    작업을 수행하면서 진행 상황을 터미널에 출력합니다.

    :param msg: 진행률 옆에 표시될 메시지
    :param total_count: 총 반복 횟수
    :param callback: 각 루프에서 실행할 함수 (인자로 현재 인덱스 전달)
    :param interval: 진행률을 갱신할 주기 (기본값: 1)
    :param eol: 작업 완료 후 개행 문자
    """

    for step in range(1, total_count + 1):
        if step % interval == 0 or step == total_count:
            progress(msg, step, total_count, eol=eol)
        callback(step - 1)
