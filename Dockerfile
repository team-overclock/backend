# 공통: uv + python 3.11
FROM ghcr.io/linuxserver/baseimage-alpine:3.23 AS base

LABEL org.opencontainers.image.base.name="ghcr.io/linuxserver/baseimage-alpine:3.23"

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



# venv 구성
FROM base AS deploy-base
RUN apk add --no-cache gdal-dev
RUN uv venv "$VIRTUAL_ENV"

# 라이브러리 설치
FROM deploy-base AS deploy-build
ENV CC=clang
ENV CXX=clang++
RUN apk add --no-cache clang compiler-rt
COPY requirements.txt .
RUN uv pip install --link-mode=copy --no-cache -r requirements.txt

# 최종
FROM deploy-base AS deploy
ENV MODE=production
COPY --from=deploy-build "$VIRTUAL_ENV" "$VIRTUAL_ENV"
COPY requirements.txt .
COPY root/ /
COPY data/url.txt ./data/url.txt
COPY app ./app
COPY scripts ./scripts
RUN sha256sum "/defaults/requirements.txt" | sed "s|/defaults|/app|" > "$VIRTUAL_ENV/.requirements.lock"
WORKDIR /app
