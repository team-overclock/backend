import csv
from pathlib import Path


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


def get_csv_files(directory_path: str) -> list[str]:
    """
    디렉토리 내의 CSV 파일 목록을 반환합니다.
    
    Args:
        directory_path (str): 디렉토리 경로
        
    Returns:
        list: CSV 파일의 절대 경로 리스트
    """

    try:
        csv_files = []
        path = Path(directory_path)
        
        if not path.exists():
            print(f"디렉토리를 찾을 수 없습니다: {directory_path}")
            return []
        
        if not path.is_dir():
            print(f"경로가 디렉토리가 아닙니다: {directory_path}")
            return []
        
        for file in path.glob("*.csv"):
            csv_files.append(str(file.absolute()))
        
        return csv_files
    except Exception as e:
        print(f"디렉토리 읽기 중 오류 발생: {e}")
        return []


def find_header_line(path: str, encoding: str) -> int:
    """
    따옴표 개수로 헤더 위치 탐지
    
    - 따옴표 2개: 메타데이터/주석(건너뛰기)
    - 위 라인 제외 후 첫 라인을 헤더로 간주

    Args:
        path (str): 파일 경로
        encoding (str): 파일 인코딩
    
    Returns:
        int: 헤더가 위치한 라인 번호 (0부터 시작)
    """

    with open(path, encoding=encoding, errors="ignore") as f:
        for i, line in enumerate(f):
            if line.count('"') == 2:
                continue
            return i
    return 0


def read_csv_file(file_path: str, column_names: list[str] | None = None) -> list[dict[str, str]]:
    """
    CSV 파일을 읽어 리스트로 반환합니다.
    
    Args:
        file_path (str): CSV 파일 경로
        column_names (list[str] | None): CSV 컬럼명을 직접 지정할 때 사용
        
    Returns:
        list: CSV 파일의 데이터를 딕셔너리 형태로 변환한 리스트
    """

    try:
        data = []
        enc = sniff_encoding(file_path)
        header_line = find_header_line(file_path, enc)
        with open(file_path, 'r', encoding=enc) as file:
            for _ in range(header_line):
                file.readline()

            reader = csv.DictReader(file, fieldnames=column_names)
            if column_names:
                next(reader, None)

            if reader.fieldnames:
                for row in reader:
                    data.append(row)
                return data
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {e}")

    return []
