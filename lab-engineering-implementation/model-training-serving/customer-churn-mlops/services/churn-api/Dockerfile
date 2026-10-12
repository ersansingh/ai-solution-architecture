# Build from the project root:  docker build -f services/churn-api/Dockerfile -t churn-api .
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/srv:/srv/src CHURN_CONFIG_DIR=/srv/config
WORKDIR /srv

COPY services/churn-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && useradd --uid 10001 --no-create-home app

# Only the feature contract, record helpers and feature formulas (what-if overrides) are needed at runtime.
COPY config/features.yaml config/project.yaml /srv/config/
COPY src/churn/__init__.py src/churn/config.py src/churn/feature_store.py src/churn/feature_engineering.py /srv/src/churn/
COPY services/churn-api/app /srv/app

USER 10001
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz')"
CMD ["uvicorn", "--factory", "app.main:create_app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2", "--no-access-log"]
