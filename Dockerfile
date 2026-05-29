# 공통: uv + python 3.11
FROM ghcr.io/linuxserver/baseimage-alpine:3.23 AS base

ENV HOME="/config"
ENV VIRTUAL_ENV="/venv"
ENV PATH="$VIRTUAL_ENV/bin:$HOME/.local/bin:$PATH"
ENV PUID=1000
ENV PGID=1000
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /uvx /usr/local/bin/
RUN uv python install 3.11

WORKDIR /defaults



# 배포용: 공통 이미지
FROM base AS deploy-base
RUN uv venv "$VIRTUAL_ENV"

# 배포용: 빌드
FROM deploy-base AS deploy-build
ENV CC=clang
ENV CXX=clang++
RUN apk add --no-cache gdal-dev clang compiler-rt
COPY requirements.txt .
RUN uv pip install --link-mode=copy --no-cache -r requirements.txt

# 배포용: 메인
FROM deploy-base AS deploy
COPY --from=deploy-build "$VIRTUAL_ENV" "$VIRTUAL_ENV"
COPY requirements.txt .
COPY root/ /
COPY data/url.txt ./data/url.txt
COPY app ./app
COPY scripts ./scripts
WORKDIR /app



# 운영용
FROM deploy AS prod
ENV MODE=production

# 개발용: main 브랜치 push 시 자동 배포되는 이미지
FROM deploy AS dev
ENV MODE=development

# 로컬 개발용 이미지
FROM base AS local
ENV MODE=local
ENV CC=clang
ENV CXX=clang++
RUN apk add --no-cache gdal-dev clang compiler-rt
COPY root/ /
VOLUME /venv
WORKDIR /app
