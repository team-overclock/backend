# 공통: uv + python 3.11
FROM ghcr.io/linuxserver/baseimage-alpine:3.23 AS base

ENV HOME="/config"
ENV VIRTUAL_ENV="/venv"
ENV PATH="$VIRTUAL_ENV/bin:$HOME/.local/bin:$PATH"
ENV PUID=1000
ENV PGID=1000
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /uvx /usr/local/bin/
RUN uv python install 3.11
COPY root/ /



# 운영용: 공통 이미지
FROM base AS prod-base
ENV APP_ENV=production
ENV UV_COMPILE_BYTECODE=1
RUN uv venv $VIRTUAL_ENV

# 운영용: 빌드
FROM prod-base AS prod-build
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt

# 운영용: 메인
FROM prod-base AS prod
COPY --from=prod-build $VIRTUAL_ENV $VIRTUAL_ENV
COPY data ./data
COPY app ./app
COPY scripts ./scripts
WORKDIR /app/scripts



# 개발용 이미지
FROM base AS dev
ENV APP_ENV=development
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app/scripts
