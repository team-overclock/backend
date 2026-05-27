import csv
from typing import TextIO, Generator

from app.utils import sniff_encoding


def iter_from_header(f: TextIO) -> Generator[str, None, None]:
    """
    CSV 상단 메타데이터/주석 라인을 건너뛰고
    헤더 라인부터 yield 합니다.

    규칙:
    - 따옴표 2개인 라인은 메타데이터/주석으로 간주
    - 그 외 첫 번째 라인을 헤더로 간주
    """
    found_header = False
    for line in f:
        if not found_header and line.count('"') == 2:
            continue
        found_header = True
        yield line


def read_csv_file(
    file_path: str,
    *,
    header: bool = True,
    fieldnames: list[str] | None = None,
    delimiter: str = ","
) -> Generator[dict[str, str], None, None]:
    """
    CSV 파일을 읽어 리스트로 반환합니다.
    
    Args:
        file_path (str): CSV 파일 경로
        has_header (bool): CSV 파일에 헤더가 포함되어 있는지 여부 (기본값: True)
        fieldnames (list[str] | None): CSV 컬럼명을 직접 지정할 때 사용
        delimiter (str): CSV 구분자 (기본값: ",")
        
    Returns:
        Generator[dict[str, str], None, None]: CSV 파일의 데이터를 딕셔너리 형태로 반환하는 제너레이터
    """

    try:
        enc = sniff_encoding(file_path)
        with open(file_path, 'r', encoding=enc) as file:
            csv.reader
            reader = csv.DictReader(
                iter_from_header(file),
                fieldnames=fieldnames,
                delimiter=delimiter,
            )
            if fieldnames and header:
                next(reader, None)
            yield from reader
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {e}")
