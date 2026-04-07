"""테스트 공통 설정 모듈.

프로젝트 루트를 `sys.path`에 추가해 `src` 패키지 import를 안정적으로 보장.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
