# LightGBM bring-your-own-container for SageMaker Training (plan G6).
#   docker build -t churn-lightgbm containers/lightgbm
#   docker tag churn-lightgbm <account>.dkr.ecr.<region>.amazonaws.com/churn-lightgbm:<tag> && docker push ...
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy==1.26.4 lightgbm==4.5.0 scikit-learn==1.5.2
ENV PYTHONUNBUFFERED=1 PATH="/opt/program:${PATH}"
COPY train /opt/program/train
RUN chmod +x /opt/program/train
WORKDIR /opt/program
# SageMaker runs `docker run <image> train`.
