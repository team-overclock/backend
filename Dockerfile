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



# 운영용 이미지
FROM base AS prod
ENV APP_ENV=production
ENV UV_COMPILE_BYTECODE=1
RUN uv venv $VIRTUAL_ENV
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt
COPY data ./data
COPY app ./app



# 개발용 이미지
FROM base AS dev
ENV APP_ENV=development
ENV PYTHONDONTWRITEBYTECODE=1
