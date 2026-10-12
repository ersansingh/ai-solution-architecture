# Architecture and implementation decisions

This document records how the build differs from, and extends, the engineering plan (`../../engineering-implementation-plan.md`).

| ID | Decision | Why |
|---|---|---|
| IMP-1 | **EKS hosts `churn-api`**, behind API Gateway REST → VPC Link → internal NLB → TargetGroupBinding (pods, target type ip). This replaces the plan's Lambda. | Requested. Gives no cold starts for the 150 ms budget, steady connection pools to the Feature Store and the endpoint, HPA, and a PDB with zone spread for 99.9% availability. |
| IMP-2 | **Terraform owns the infrastructure; the deploy state machine owns endpoints; Helm owns the app** | Endpoints change with every approved model version, so Terraform would fight the deploy state machine over them. Terraform passes Helm the IRSA role and target group through the `churn_api_helm_values` output. |
| IMP-3 | **`config/features.yaml` is the single feature contract** | Terraform builds the Feature Group schema and drift-alarm metric names from it. Python uses it for preprocessing and encoded names. churn-api uses it for the request vector order. |
| IMP-4 | **Fixed one-hot vocabularies and explicit missing indicators** | Encoded column names are known when the pipeline is defined, which Clarify headers need. They're also stable between training and serving. |
| IMP-5 | **The `ChurnPreprocessor` state is plain dicts** | The artifact unpickles in both the scikit-learn 1.2-1 serving image and the local image. |
| IMP-6 | **Threshold travels in `evaluation.json` → SSM** | The pipeline can't put a runtime value into the registry metadata. `publish_serving_config` reads it from the package's model-quality metrics. |
| IMP-7 | **What-if overrides recompute engineered features** in churn-api | A support agent who changes `satisfaction_score` also changes `customer_risk_score`. |
| IMP-8 | **Clarify bias uses a static 0.5 threshold** | `ModelPredictedLabelConfig` needs a value when the pipeline is defined. The serving threshold is applied downstream. |
| IMP-9 | **LocalStack Community + stand-ins** (model-server, DynamoDB, SQS) | Free edition; see the README table. The AWS-native parts use the same Terraform modules. |
| IMP-10 | **Synthetic generator `SIGNAL_STRENGTH = 2.5`** | Gives AUC of about 0.98, so precision > 85% and recall > 80% are reachable at 18% prevalence. Lower it to rehearse a failing gate. |

## Request path latency (p99 budget, plan section 6.3)

| Hop | Budget |
|---|---|
| API Gateway + VPC Link + NLB | 20 ms |
| churn-api validation and override recompute | 5 ms |
| Feature Store `GetRecord` (VPC endpoint) | 15 ms |
| `InvokeEndpoint` (PipelineModel, 2 containers) | 50 ms (`churn-prod-model-latency-p99` alarm) |
| Headroom | 60 ms |

In the local stack, 200 sequential requests through churn-api → DynamoDB → model-server had a p99 well under 150 ms. A typical request took about 13 ms.

## Known limitations

* LocalStack doesn't emulate the SageMaker parts (Pipeline, Clarify, Debugger, Model Monitor, Batch Transform) or EKS. They're exercised by unit tests (Lambdas with botocore Stubber) and by `pipelines/pipeline.py --validate` against a real account.
* Model Monitor names drift metrics after column positions (`feature_baseline_drift__c<N>`) because captured CSV has no header. Terraform maps feature names to positions for numeric features only.
* Each Pipeline execution copies the whole `raw-data/` prefix into the Processing job, and the job reads the newest partition per source. Add an S3 lifecycle rule or archive old partitions as history grows.
