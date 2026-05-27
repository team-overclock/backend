# backend

개발 환경의 Python 버전은 `3.11.9`임을 참고해 주세요.

## 구조

- `data/`: 데이터베이스에 삽입할 csv 파일 저장 폴더
- `diagram/`: 데이터베이스 다이어그램 파일 및 이미지 (참고용)
- `app/main.py`: FastAPI 앱 생성/설정, 실행 진입점
- `app/database.py`: DB 세션 연결 함수
- `app/crud/`: CRUD(create, read, update, delete)
- `app/core/`: 코어?
- `app/models/`: DB 모델
- `app/routers/`: 기능별 라우터
- `app/schemas/`: 요청/응답 스키마
- `tests/`: 앱 테스트 케이스 코드
- `root/`: 도커 이미지 빌드 시 루트 경로에 복사할 대상 폴더
- `scripts/`: 파이썬/bash 스크립트 파일, 상단에 `#!`로 시작한다면 컨테이너 내에서 명령어로 변환됨

## requirements.txt

필요한 라이브러리 목록을 해당 파일에 나열

## 설치

> [!NOTE]
> `requirements-dev.txt` 파일 지정 시
> [테스트](#테스트) 및 [insert-data](#insert-data)
> 작업에 사용되는 라이브러리까지 같이 설치됨

나열된 목록을 한 번에 설치

```shell
pip install -r requirements.txt
```

## 실행

```shell
fastapi run app
# 또는 python3 -m fastapi run app
```

### 개발모드로 실행

실행 중 코드 변경 시 즉시 반영됨

```shell
fastapi dev app
# 또는 python3 -m fastapi dev app
```

## Docker

> [!NOTE]
> 도커 컨테이너 실행 방법은
> [team-overclock/monorepo#docker](https://github.com/team-overclock/monorepo#docker)
> 참고

내장 명령어 목록 및 설명

### create user

데이터베이스에 사용자 추가

```shell
# name 생략 시 "@" 앞부분을 name으로 삽입
docker exec -it <container_name> create-user <email> [name]
```

### insert data

> [!IMPORTANT]
> 도커 이미지 경량화를 위해 제거되었으며,
> 파이썬으로 직접 파일을 실행할 수 있습니다.

> [!IMPORTANT]
> [url.txt](data/url.txt) 파일 내 구글 드라이브에서 모든 파일 다운로드

`data` 폴더 내 csv 파일 내 데이터를 데이터베이스에 삽입 (테이블 자동 생성)

```shell
python3 scripts/insert_data.py
# docker exec -it <container_name> insert-data  # deprecated
```

### insert seeds

> [!IMPORTANT]
> `insert-data`가 먼저 수행되어야 함

> [!NOTE]
> 게스트 유저는 항상 생성되며,
> `num_of_users`에 포함되지 않음

데이터베이스에 랜덤 사용자 및 추천 데이터 삽입.

```shell
# num_of_recs 기본값: 30
# num_of_users 기본값: 0

python3 scripts/insert_seeds.py [num_of_recs] [num_of_users]
# or
docker exec -it <container_name> insert-seeds [num_of_recs] [num_of_users]
```

### drop seeds

> [!NOTE]
> 게스트 계정과 property_infrastructure 테이블 데이터는 삭제되지 않음

생성된 seed 데이터 삭제.

```shell
python3 scripts/drop_seeds.py
# or
docker exec -it <container_name> drop-seeds
```

### drop tables

데이블 삭제

```shell
python3 scripts/drop_tables.py [-y|--yes]
# or
docker exec -it <container_name> drop-tables [-y|--yes]
```

연결된 데이터베이스의 모든 테이블 삭제.
`-y` 또는 `--yes` 입력 시 삭제 여부를 묻지 않고 즉시 삭제함.

### drop to seeds

`drop-tables`, `insert-data`, `insert-seeds`를 연속으로 실행하는 스크립트

```shell
docker exec -it <container_name> drop-to-seeds
```

## 테스트

API 서버가 정상 작동하는지 테스트 자동화

```shell
pytest -q
```

특정 파일만 실행:

```shell
pytest -q tests/test_health.py
```

## API 문서

- <http://127.0.0.1:8000/docs>:
  fastapi 기본 제공,
  swagger-ui, 엔드포인트 목록 및 테스트 가능
- <http://127.0.0.1:8000/redoc>:
  fastapi 기본 제공,
  swagger-ui보다 가독성은 좋으나 요청 테스트 등 기능 없음
- <http://127.0.0.1:8000/scalar>:
  swagger-ui대안,
  가독성 좋으면서 요청 테스트도 가능한 문서,
  언어/명령어별 요청 예시 코드 제공
