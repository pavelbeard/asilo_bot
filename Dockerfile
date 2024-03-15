FROM python:3.12.1-slim-bookworm

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt