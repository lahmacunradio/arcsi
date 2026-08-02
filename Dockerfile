FROM python:3.11.13-slim-bullseye AS builder

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
RUN pip3 install -r requirements.txt

FROM build AS init
EXPOSE 5666
RUN ["chmod", "+x", "./entrypoint.sh"]
ENTRYPOINT []
