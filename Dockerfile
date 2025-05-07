FROM python:3.13-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ADD requirements.txt /app/
WORKDIR /app

RUN apt-get update \
    && apt-get install gcc g++ \
    libblas-dev libffi-dev liblapack-dev libopenblas-dev libpq-dev \
    musl-dev postgresql tmpreaper -y \
    && apt-get clean \
    && pip3 install --upgrade pip  \
    && pip3 install -r requirements.txt

ADD infra/tmpreaper.conf /etc/tmpreaper.conf

ADD . /app

EXPOSE 5666

RUN ["chmod", "+x", "/app/entrypoint.sh"]
ENTRYPOINT []
