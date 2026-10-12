# Local ML image: synthetic data, preprocessing, XGBoost training and the model server.
# Build from the project root: docker build -f local/Dockerfile.ml -t churn-ml .
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/srv/src:/srv/services/model-server \
    CHURN_CONFIG_DIR=/srv/config
WORKDIR /srv
COPY local/requirements-ml.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY config /srv/config
COPY src /srv/src
COPY services/model-server /srv/services/model-server
COPY scripts /srv/scripts
EXPOSE 8080
CMD ["uvicorn", "--factory", "server:create_app", "--host", "0.0.0.0", "--port", "8080"]
