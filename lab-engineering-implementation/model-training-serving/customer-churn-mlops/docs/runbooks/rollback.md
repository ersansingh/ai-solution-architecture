# Runbook: model rollback

## Automatic (during a deployment)

The prod endpoint update uses `BlueGreenUpdatePolicy` (canary 10%) with `AutoRollbackConfiguration` on:

* `churn-prod-5xx-rollback`: endpoint 5XX above 5% for 2 minutes
* `churn-prod-latency-rollback`: model p99 latency above 300 ms (300,000 µs) for 2 minutes

If either fires during the bake window, SageMaker moves traffic back to the blue fleet. The state machine's `endpoint_status` step sees that the endpoint is `InService` on the **old** config, and goes to `NotifyRollback` (SNS) and `DeploymentFailed`. The serving config in SSM isn't changed, so churn-api keeps using the previous threshold.

**Rollback test (Phase 10, AT-10).** Register a version whose evaluation passes but whose serving fails. For example, set the `SAGEMAKER_PROGRAM` env of container 1 to a missing script, or ship a preprocessor that raises on 10% of rows. Approve it, then send traffic with `tests/load/locustfile.py`. Expected result: the canary errors, the alarm fires, the endpoint config returns to the previous one, and an SNS "rolled back automatically" message arrives.

## Manual (after a deployment completed)

1. In the Model Registry, set the **bad** version to `Rejected`.
2. Set the **previous good** version to `Approved` again. That emits the approval event and the state machine redeploys it, including staging smoke tests.
3. For speed, you can instead run `aws stepfunctions start-execution` with input `{"detail": {"ModelPackageArn": "<previous arn>"}}`.
4. Check that `/teleconnect-churn/prod/serving-config` shows the previous `model_version`. churn-api picks it up within 60 s, the SSM cache TTL.

## churn-api (EKS) rollback

Run `helm rollback churn-api <revision> -n churn`. `helm history churn-api -n churn` lists the revisions. The deploy workflow uses `--atomic`, so a failed upgrade rolls itself back.
