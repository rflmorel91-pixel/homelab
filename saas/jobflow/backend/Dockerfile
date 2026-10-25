FROM python:3.14-slim

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
       libpq5 \
       passwd \
    && groupadd --system --gid 10001 jobflow \
    && useradd --system --uid 10001 --gid 10001 \
       --home-dir /app --no-create-home --shell /usr/sbin/nologin jobflow \
    && install -d --owner=10001 --group=10001 --mode=0750 \
       /var/lib/jobflow-private/prestamodesk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip uninstall -y pip

COPY app ./app
COPY alembic.ini .
COPY scripts ./scripts

EXPOSE 8001

USER 10001:10001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
