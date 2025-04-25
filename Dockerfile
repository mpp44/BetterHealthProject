FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY pyproject.toml poetry.lock* /app/
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-root

COPY . /app/
RUN chmod +x /app/entrypoint.sh
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]