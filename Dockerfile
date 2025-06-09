FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY pyproject.toml poetry.lock* /app/
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root

COPY . /app/
RUN apt-get update && apt-get install -y dos2unix && dos2unix /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]