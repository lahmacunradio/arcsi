FROM python:3.12-slim-trixie AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install gcc g++ \
    libblas-dev libffi-dev liblapack-dev libopenblas-dev libpq-dev \
    musl-dev postgresql tmpreaper -y \
    && apt-get clean
ADD infra/tmpreaper.conf /etc/tmpreaper.conf

FROM builder AS build
WORKDIR /app
ADD . .
RUN uv lock

FROM build AS init
EXPOSE 5666
RUN ["chmod", "+x", "./entrypoint.sh"]
ENTRYPOINT []
