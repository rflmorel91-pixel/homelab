FROM python:3.14-alpine3.24 AS builder
RUN apk add --no-cache build-base libffi-dev postgresql-dev
WORKDIR /build
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --prefix=/install -r requirements.txt
RUN python -m pip install --no-cache-dir --prefix=/install "psycopg[c]==3.3.4"

FROM python:3.14-alpine3.24
RUN apk upgrade --no-cache \
    && apk add --no-cache libpq ca-certificates \
    && addgroup -S -g 10001 jobflow \
    && adduser -S -D -H -u 10001 -G jobflow jobflow \
    && mkdir -p /var/lib/jobflow-private/prestamodesk \
    && chown 10001:10001 /var/lib/jobflow-private/prestamodesk \
    && chmod 0750 /var/lib/jobflow-private/prestamodesk

COPY --from=builder /install /usr/local
RUN python -m pip uninstall -y pip

WORKDIR /app
COPY app ./app
COPY alembic.ini .
COPY scripts ./scripts

ENV PYTHONDONTWRITEBYTECODE=1
USER 10001:10001
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
