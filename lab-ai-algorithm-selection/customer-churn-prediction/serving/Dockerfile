# syntax=docker/dockerfile:1.7
# KServe custom transformer: Feast lookup, precomputed/rescoring routing,
# isotonic calibration and in-process TreeSHAP reason codes. Context: serving/
#
# Feast client config comes from the single source of truth features/feature_store.yaml
# via a named build context (CI: docker/build-push-action `build-contexts`):
#   docker buildx build --build-context features=features/ -f serving/Dockerfile serving/
FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FEAST_REPO_PATH=/app/feature_repo

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY churn_serving/ ./churn_serving/
# Only feature_store.yaml is needed at runtime: definitions are read from the
# shared registry (feast apply in CI), the transformer only reads the online store.
COPY --from=features feature_store.yaml ./feature_repo/feature_store.yaml

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin kserve \
    && chown -R 10001:10001 /app
USER 10001

EXPOSE 8080
ENTRYPOINT ["python", "-m", "churn_serving"]
