# TeleConnect churn MLOps - common tasks. Run from this directory.
PY        ?= python3
VENV      ?= .venv
BIN        = $(VENV)/bin
COMPOSE    = docker compose -f local/docker-compose.yml
TF_AWS     = infra/terraform/envs/aws
REGION    ?= us-east-1
IMAGE_TAG ?= $(shell git rev-parse --short HEAD)

.PHONY: help venv lint test train-local local-up local-test local-down local-logs k3d-up k3d-deploy \
        tf-fmt tf-validate tf-plan tf-apply pipeline-validate pipeline-upsert pipeline-start \
        api-image api-push api-deploy lightgbm-push batch monitoring teardown

help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

venv: ## Create the virtualenv with dev dependencies
	$(PY) -m venv $(VENV) && $(BIN)/pip install -U pip && $(BIN)/pip install -r requirements-dev.txt

lint: ## flake8 + terraform fmt check
	$(BIN)/flake8 src services pipelines deployment scripts tests
	terraform fmt -check -recursive infra/terraform

test: ## Unit tests (no AWS, no Docker)
	$(BIN)/pytest

train-local: ## Generate data + preprocess + train + evaluate locally (ROWS=200000)
	PYTHONPATH=src $(BIN)/python -m churn.jobs.local_train --rows $${ROWS:-200000} --work local/work

# ---- local stack: LocalStack + Terraform(envs/local) + model-server + churn-api -----------------
local-up: ## Start the local stack in Docker
	$(COMPOSE) up -d --build churn-api
	$(COMPOSE) ps

local-test: ## Run integration tests from the Docker test container
	$(COMPOSE) --profile test run --rm --build tests

local-logs:
	$(COMPOSE) logs -f churn-api model-server

local-down: ## Stop the local stack and drop volumes
	$(COMPOSE) --profile test down -v
	rm -f infra/terraform/envs/local/terraform.tfstate*

k3d-up: ## Optional: local Kubernetes (EKS stand-in) running the Helm chart against the local stack
	k3d cluster create churn --agents 2 --k3s-arg "--disable=traefik@server:0" || true
	docker build -f services/churn-api/Dockerfile -t churn-api:local .
	k3d image import churn-api:local -c churn

k3d-deploy: ## Install deploy/helm/churn-api with values-local.yaml on k3d
	helm upgrade --install churn-api deploy/helm/churn-api -n churn --create-namespace -f deploy/helm/churn-api/values-local.yaml
	kubectl -n churn rollout status deploy/churn-api

# ---- AWS ----------------------------------------------------------------------------------------
tf-fmt:
	terraform fmt -recursive infra/terraform

tf-validate: ## terraform validate both environments (no credentials needed)
	cd infra/terraform/envs/local && terraform init -backend=false -input=false >/dev/null && terraform validate
	cd $(TF_AWS) && terraform init -backend=false -input=false >/dev/null && terraform validate

tf-plan:
	cd $(TF_AWS) && terraform init -backend-config=backend.hcl && terraform plan -out=tfplan

tf-apply:
	cd $(TF_AWS) && terraform apply tfplan

pipeline-validate: ## Build the SageMaker Pipeline definition (needs AWS credentials)
	$(BIN)/python pipelines/pipeline.py --validate

pipeline-upsert:
	$(BIN)/python pipelines/pipeline.py --upsert

pipeline-start:
	$(BIN)/python pipelines/pipeline.py --upsert --start --git-sha $(IMAGE_TAG)

api-image:
	docker build -f services/churn-api/Dockerfile -t churn-api:$(IMAGE_TAG) .

api-push: api-image ## Push churn-api to ECR
	$(eval REPO := $(shell cd $(TF_AWS) && terraform output -json ecr_repository_urls | $(PY) -c "import json,sys; print(json.load(sys.stdin)['churn-api'])"))
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(firstword $(subst /, ,$(REPO)))
	docker tag churn-api:$(IMAGE_TAG) $(REPO):$(IMAGE_TAG) && docker push $(REPO):$(IMAGE_TAG)

api-deploy: ## helm upgrade churn-api on EKS with Terraform-provided values
	$(eval REPO := $(shell cd $(TF_AWS) && terraform output -json ecr_repository_urls | $(PY) -c "import json,sys; print(json.load(sys.stdin)['churn-api'])"))
	cd $(TF_AWS) && terraform output -raw churn_api_helm_values > $(CURDIR)/values-aws.yaml
	aws eks update-kubeconfig --name $$(cd $(TF_AWS) && terraform output -raw eks_cluster_name) --region $(REGION)
	helm upgrade --install churn-api deploy/helm/churn-api -n churn -f values-aws.yaml \
	  --set image.repository=$(REPO) --set image.tag=$(IMAGE_TAG) --wait --timeout 10m

lightgbm-push: ## Build + push the LightGBM BYOC training image
	$(eval REPO := $(shell cd $(TF_AWS) && terraform output -json ecr_repository_urls | $(PY) -c "import json,sys; print(json.load(sys.stdin)['churn-lightgbm'])"))
	docker build -t $(REPO):$(IMAGE_TAG) containers/lightgbm && docker push $(REPO):$(IMAGE_TAG)

batch: ## Score all customers with Batch Transform (RUN_DATE=YYYY-MM-DD)
	$(BIN)/python deployment/batch_transform.py --run-date $${RUN_DATE:-$$(date +%F)}

monitoring: ## Create Model Monitor schedules on the prod endpoint
	$(BIN)/python deployment/monitoring.py

teardown: ## Dry-run delete of endpoints/monitors (add ARGS=--yes)
	$(BIN)/python scripts/teardown.py $(ARGS)
