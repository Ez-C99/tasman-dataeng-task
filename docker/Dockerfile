# ---- Build stage: resolve wheels in an isolated layer
FROM python:3.12-slim AS build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip wheel --no-cache-dir --wheel-dir /wheels .

# ---- Runtime stage: minimal, non-root, deterministic
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd -u 10001 -m appuser
COPY --from=build /wheels /wheels
RUN pip install --no-cache /wheels/*
COPY app /app/app
COPY README.md /app/
USER appuser
ENTRYPOINT ["python", "-m", "app.tasman_etl.runner.run"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python - <<'PY'\nimport importlib; importlib.import_module('app.tasman_etl.runner.run'); print('ok')\nPY
