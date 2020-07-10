FROM python:3.8-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ADD requirements.txt /app/
WORKDIR /app

RUN apt-get update \
    && apt-get install gcc g++ \
    libblas-dev libffi-dev liblapack-dev libopenblas-dev libpq-dev \
    musl-dev postgresql -y \
    && apt-get clean \
    && pip3 install -r requirements.txt

ADD . /app

EXPOSE 5666

RUN ["chmod", "+x", "/app/entrypoint.sh"]
ENTRYPOINT []