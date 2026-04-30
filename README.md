# backend

## 구조

- `app/main.py`: FastAPI 앱 생성/설정, 실행 진입점
- `app/crud.py`: DB crud(create, read, update, delete)
- `app/database.py`: DB 세션 연결 함수
- `app/core/`: 코어?
- `app/models/`: DB 모델
- `app/routers/`: 기능별 라우터
- `app/schemas/`: 요청/응답 스키마

## requirements.txt

필요한 라이브러리 목록을 해당 파일에 나열

## 설치

나열된 목록을 한 번에 설치

```shell
pip install -r requirements.txt
```

## 실행

```shell
fastapi dev app
# 또는 python3 -m fastapi dev app
```

### Docker

도커 관련 사용법은
[team-overclock/monorepo#docker](https://github.com/team-overclock/monorepo#docker)
참고

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

### FastAPI 내장

- <http://127.0.0.1:8000/docs>:
  fastapi 기본 제공,
  swagger-ui, 엔드포인트 목록 및 테스트 가능
- <http://127.0.0.1:8000/redoc>:
  fastapi 기본 제공,
  swagger-ui보다 가독성은 좋으나 요청 테스트 등 기능 없음
- <http://127.0.0.1:8000/scalar>:
  swagger-ui대안,
  가독성은 좋은 요청 테스트도 가능한 문서,
  언어별 요청 예시 코드 제공
