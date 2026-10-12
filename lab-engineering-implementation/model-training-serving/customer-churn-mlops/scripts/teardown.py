"""Lab cost control (plan section 11): delete what Terraform does not own.

Endpoints, endpoint configs and models created by the deploy state machine, and Model Monitor
schedules. Run before `terraform destroy`.

  python scripts/teardown.py [--yes]
"""
from __future__ import annotations

import argparse

import boto3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="actually delete (default: dry run)")
    args = parser.parse_args()
    sm = boto3.client("sagemaker")

    schedules = [s["MonitoringScheduleName"] for s in sm.list_monitoring_schedules(
        NameContains="customer-churn")["MonitoringScheduleSummaries"]]
    endpoints = [e["EndpointName"] for e in sm.list_endpoints(NameContains="customer-churn")["Endpoints"]]
    configs = [c["EndpointConfigName"] for c in sm.list_endpoint_configs(NameContains="churn-")["EndpointConfigs"]]
    models = [m["ModelName"] for m in sm.list_models(NameContains="churn-")["Models"]]
    plan = {"monitoring_schedules": schedules, "endpoints": endpoints, "endpoint_configs": configs, "models": models}
    for kind, names in plan.items():
        print(f"{kind}: {names}")
    if not args.yes:
        print("dry run - pass --yes to delete")
        return
    for name in schedules:
        sm.delete_monitoring_schedule(MonitoringScheduleName=name)
    for name in endpoints:
        sm.delete_endpoint(EndpointName=name)
    for name in configs:
        sm.delete_endpoint_config(EndpointConfigName=name)
    for name in models:
        sm.delete_model(ModelName=name)
    print("deleted")


if __name__ == "__main__":
    main()
