# ---- Build stage: build wheels for deps + our project
FROM python:3.12-slim AS build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
COPY src ./src
RUN pip install --upgrade pip && pip wheel --no-cache-dir --wheel-dir /wheels .

# ---- Runtime stage: slim, non-root, install wheels
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd -u 10001 -m appuser
COPY --from=build /wheels /wheels
RUN pip install --no-cache /wheels/*
USER appuser
ENTRYPOINT ["python", "-m", "tasman_etl.runner.run"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python - <<'PY'\nimport importlib; importlib.import_module('tasman_etl.runner.run'); print('ok')\nPY
