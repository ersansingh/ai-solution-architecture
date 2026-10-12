"""SageMaker Pipeline `CustomerChurnPipeline` (plan section 6.5, milestone M8).

Preprocess -> IngestFeatures (parallel) -> DataQualityBaseline -> TrainXGBoost (Debugger rules)
-> Evaluate -> CreateClarifyModel -> ClarifyExplainability / ClarifyBias -> GateKPIs
-> RegisterModel (PipelineModel: sklearn preprocessor + XGBoost, PendingManualApproval) | FailOnGate

  python pipelines/pipeline.py --validate              # build definition, print JSON (needs AWS creds:
                                                       #   source bundles are uploaded at build time)
  python pipelines/pipeline.py --upsert [--start] [--git-sha SHA] [--with-tuning]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import sagemaker  # noqa: E402
from sagemaker import image_uris  # noqa: E402
from sagemaker.clarify import BiasConfig, DataConfig, ModelConfig, ModelPredictedLabelConfig, SHAPConfig  # noqa: E402
from sagemaker.debugger import Rule, rule_configs  # noqa: E402
from sagemaker.drift_check_baselines import DriftCheckBaselines  # noqa: E402
from sagemaker.estimator import Estimator  # noqa: E402
from sagemaker.inputs import TrainingInput  # noqa: E402
from sagemaker.model import Model  # noqa: E402
from sagemaker.model_metrics import MetricsSource, ModelMetrics  # noqa: E402
from sagemaker.model_monitor import DatasetFormat  # noqa: E402
from sagemaker.pipeline import PipelineModel  # noqa: E402
from sagemaker.processing import FrameworkProcessor, ProcessingInput, ProcessingOutput  # noqa: E402
from sagemaker.sklearn.estimator import SKLearn  # noqa: E402
from sagemaker.sklearn.model import SKLearnModel  # noqa: E402
from sagemaker.tuner import HyperparameterTuner  # noqa: E402
from sagemaker.workflow.check_job_config import CheckJobConfig  # noqa: E402
from sagemaker.workflow.clarify_check_step import (  # noqa: E402
    ClarifyCheckStep,
    ModelBiasCheckConfig,
    ModelExplainabilityCheckConfig,
)
from sagemaker.workflow.condition_step import ConditionStep  # noqa: E402
from sagemaker.workflow.conditions import ConditionEquals, ConditionGreaterThanOrEqualTo  # noqa: E402
from sagemaker.workflow.execution_variables import ExecutionVariables  # noqa: E402
from sagemaker.workflow.fail_step import FailStep  # noqa: E402
from sagemaker.workflow.functions import Join, JsonGet  # noqa: E402
from sagemaker.workflow.model_step import ModelStep  # noqa: E402
from sagemaker.workflow.parameters import (  # noqa: E402
    ParameterBoolean,
    ParameterFloat,
    ParameterString,
)
from sagemaker.workflow.pipeline import Pipeline  # noqa: E402
from sagemaker.workflow.pipeline_context import PipelineSession  # noqa: E402
from sagemaker.workflow.properties import PropertyFile  # noqa: E402
from sagemaker.workflow.quality_check_step import DataQualityCheckConfig, QualityCheckStep  # noqa: E402
from sagemaker.workflow.steps import CacheConfig, ProcessingStep, TrainingStep, TuningStep  # noqa: E402
from sagemaker.xgboost.estimator import XGBoost  # noqa: E402

from churn import config  # noqa: E402
from churn.preprocessing import transformed_feature_names  # noqa: E402

PREPROCESS_OUTPUTS = ["train", "validation", "test", "test_raw", "clarify", "baseline", "features", "model", "report"]
BUNDLE_DIR = ROOT / "build" / "bundle"


def build_source_bundle() -> str:
    """churn package + config + bundle-root entry points, uploaded as each step's source_dir."""
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    shutil.copytree(ROOT / "src" / "churn", BUNDLE_DIR / "churn",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(ROOT / "config", BUNDLE_DIR / "config")
    for entry in (ROOT / "pipelines" / "entrypoints").iterdir():
        shutil.copy(entry, BUNDLE_DIR / entry.name)
    return str(BUNDLE_DIR)


def get_pipeline(role: str, bucket: str, region: str, with_tuning: bool = False) -> Pipeline:
    cfg = config.project()
    gates = config.quality_gates()
    feats = config.features()
    session = PipelineSession(default_bucket=bucket)
    bundle = build_source_bundle()
    code_location = f"s3://{bucket}/{cfg['prefixes']['pipelines']}/code"
    cache = CacheConfig(enable_caching=True, expire_after="P30D")
    run_prefix = ["s3:/", bucket, cfg["prefixes"]["training"], ExecutionVariables.PIPELINE_EXECUTION_ID]
    artifacts_prefix = ["s3:/", bucket, cfg["prefixes"]["artifacts"], ExecutionVariables.PIPELINE_EXECUTION_ID]

    # ---- parameters -------------------------------------------------------------------------
    input_data = ParameterString("InputDataUri", default_value=f"s3://{bucket}/{cfg['prefixes']['raw']}")
    processing_type = ParameterString("ProcessingInstanceType", default_value=cfg["instance_types"]["processing"])
    training_type = ParameterString("TrainingInstanceType", default_value=cfg["instance_types"]["training"])
    approval = ParameterString("ModelApprovalStatus", default_value="PendingManualApproval")
    git_sha = ParameterString("GitSha", default_value="unknown")
    auc_min = ParameterFloat("AucThreshold", default_value=float(gates["auc"]))
    precision_min = ParameterFloat("PrecisionThreshold", default_value=float(gates["precision"]))
    recall_min = ParameterFloat("RecallThreshold", default_value=float(gates["recall"]))
    skip_checks = ParameterBoolean("SkipBaselineChecks", default_value=True)
    register_baselines = ParameterBoolean("RegisterNewBaselines", default_value=True)

    # ---- Preprocess ---------------------------------------------------------------------------
    sklearn_processor = FrameworkProcessor(
        estimator_cls=SKLearn, framework_version=cfg["framework_versions"]["sklearn"], role=role,
        instance_type=processing_type, instance_count=1, base_job_name="churn-preprocess",
        code_location=code_location, sagemaker_session=session,
    )
    step_preprocess = ProcessingStep(
        name="Preprocess",
        step_args=sklearn_processor.run(
            code="preprocess.py", source_dir=bundle,
            inputs=[ProcessingInput(source=input_data, destination="/opt/ml/processing/input/raw-data")],
            outputs=[ProcessingOutput(output_name=name, source=f"/opt/ml/processing/output/{name}",
                                      destination=Join(on="/", values=run_prefix + [name]))
                     for name in PREPROCESS_OUTPUTS],
        ),
        cache_config=cache,
    )
    out = {name: step_preprocess.properties.ProcessingOutputConfig.Outputs[name].S3Output.S3Uri
           for name in PREPROCESS_OUTPUTS}

    # ---- IngestFeatures (runs in parallel with training) -----------------------------------------
    step_ingest = ProcessingStep(
        name="IngestFeatures",
        step_args=sklearn_processor.run(
            code="ingest_features.py", source_dir=bundle,
            inputs=[ProcessingInput(source=out["features"], destination="/opt/ml/processing/input/features")],
            arguments=["--feature-group", cfg["feature_group_name"], "--region", region],
        ),
    )

    # ---- Data-quality baseline for Model Monitor ----------------------------------------------
    check_job = CheckJobConfig(role=role, instance_count=1, instance_type="ml.m5.xlarge",
                               volume_size_in_gb=60, sagemaker_session=session)
    step_data_quality = QualityCheckStep(
        name="DataQualityBaseline",
        quality_check_config=DataQualityCheckConfig(
            baseline_dataset=out["baseline"], dataset_format=DatasetFormat.csv(header=False),
            output_s3_uri=Join(on="/", values=artifacts_prefix + ["data-quality"]),
        ),
        check_job_config=check_job, skip_check=skip_checks, register_new_baseline=register_baselines,
        model_package_group_name=cfg["model_package_group"],
    )

    # ---- Train / tune XGBoost with Debugger rules -------------------------------------------
    xgb_image = image_uris.retrieve("xgboost", region, cfg["framework_versions"]["xgboost"])
    xgb = Estimator(
        image_uri=xgb_image, role=role, instance_count=1, instance_type=training_type,
        output_path=f"s3://{bucket}/{cfg['prefixes']['models']}", base_job_name="churn-xgboost",
        sagemaker_session=session,
        rules=[Rule.sagemaker(rule_configs.loss_not_decreasing()), Rule.sagemaker(rule_configs.overtraining()),
               Rule.sagemaker(rule_configs.overfit()), Rule.sagemaker(rule_configs.tree_depth()),
               Rule.sagemaker(rule_configs.class_imbalance()),
               Rule.sagemaker(rule_configs.feature_importance_overweight())],
    )
    xgb.set_hyperparameters(**config.best_hparams())
    channels = {"train": TrainingInput(out["train"], content_type="text/csv"),
                "validation": TrainingInput(out["validation"], content_type="text/csv")}
    if with_tuning:
        from churn.experiments.tune import RANGES

        tuner = HyperparameterTuner(xgb, "validation:auc", RANGES, objective_type="Maximize",
                                    strategy="Bayesian", early_stopping_type="Auto",
                                    max_jobs=30, max_parallel_jobs=5)
        step_train = TuningStep(name="TuneXGBoost", step_args=tuner.fit(channels), cache_config=cache)
        model_data = step_train.get_top_model_s3_uri(top_k=0, s3_bucket=bucket,
                                                     prefix=cfg["prefixes"]["models"])
    else:
        step_train = TrainingStep(name="TrainXGBoost", step_args=xgb.fit(channels), cache_config=cache)
        model_data = step_train.properties.ModelArtifacts.S3ModelArtifacts

    # ---- Evaluate -----------------------------------------------------------------------------
    evaluation = PropertyFile(name="EvaluationReport", output_name="evaluation", path="evaluation.json")
    xgb_processor = FrameworkProcessor(
        estimator_cls=XGBoost, framework_version=cfg["framework_versions"]["xgboost"], role=role,
        instance_type="ml.m5.xlarge", instance_count=1, base_job_name="churn-evaluate",
        code_location=code_location, sagemaker_session=session,
    )
    step_evaluate = ProcessingStep(
        name="Evaluate",
        step_args=xgb_processor.run(
            code="evaluate.py", source_dir=bundle,
            inputs=[ProcessingInput(source=model_data, destination="/opt/ml/processing/model"),
                    ProcessingInput(source=out["validation"], destination="/opt/ml/processing/validation"),
                    ProcessingInput(source=out["test"], destination="/opt/ml/processing/test")],
            outputs=[ProcessingOutput(output_name="evaluation", source="/opt/ml/processing/evaluation",
                                      destination=Join(on="/", values=artifacts_prefix + ["evaluation"]))],
            arguments=["--auc", auc_min.to_string(), "--precision", precision_min.to_string(),
                       "--recall", recall_min.to_string(),
                       "--target-recall", str(gates["threshold_target_recall"]),
                       "--max-auc-regression", str(gates["max_auc_regression"]),
                       "--model-package-group", cfg["model_package_group"]],
        ),
        property_files=[evaluation],
    )
    evaluation_uri = Join(on="/", values=[
        step_evaluate.properties.ProcessingOutputConfig.Outputs["evaluation"].S3Output.S3Uri, "evaluation.json"])

    # ---- Clarify: SHAP + bias on the encoded matrix ------------------------------------------
    xgb_model = Model(image_uri=xgb_image, model_data=model_data, role=role, sagemaker_session=session)
    step_clarify_model = ModelStep(name="CreateClarifyModel",
                                   step_args=xgb_model.create(instance_type="ml.m5.xlarge"))
    clarify_data = DataConfig(
        s3_data_input_path=out["clarify"], s3_output_path=Join(on="/", values=artifacts_prefix + ["clarify"]),
        label=feats["label"], headers=[feats["label"]] + transformed_feature_names(), dataset_type="text/csv",
    )
    clarify_model = ModelConfig(model_name=step_clarify_model.properties.ModelName, instance_type="ml.m5.xlarge",
                                instance_count=1, accept_type="text/csv", content_type="text/csv")
    step_explain = ClarifyCheckStep(
        name="ClarifyExplainability",
        clarify_check_config=ModelExplainabilityCheckConfig(
            data_config=clarify_data, model_config=clarify_model,
            explainability_config=SHAPConfig(num_clusters=10, num_samples=100, agg_method="mean_abs",
                                             save_local_shap_values=True),
        ),
        check_job_config=check_job, skip_check=skip_checks, register_new_baseline=register_baselines,
        model_package_group_name=cfg["model_package_group"],
    )
    facets = feats["bias_facets"]
    step_bias = ClarifyCheckStep(
        name="ClarifyBias",
        clarify_check_config=ModelBiasCheckConfig(
            data_config=clarify_data, model_config=clarify_model,
            data_bias_config=BiasConfig(label_values_or_threshold=[1],
                                        facet_name=[f["name"] for f in facets],
                                        facet_values_or_threshold=[f["value_or_threshold"] for f in facets]),
            # Clarify needs a static threshold at definition time; the serving threshold
            # chosen in Evaluate is applied by churn-api / batch post-processing.
            model_predicted_label_config=ModelPredictedLabelConfig(probability_threshold=0.5),
        ),
        check_job_config=check_job, skip_check=skip_checks, register_new_baseline=register_baselines,
        model_package_group_name=cfg["model_package_group"],
    )

    # ---- Register the serving PipelineModel -------------------------------------------------
    preprocessor_model = SKLearnModel(
        model_data=Join(on="/", values=[out["model"], "model.tar.gz"]), role=role,
        entry_point="serve_preprocessor.py", source_dir=bundle,
        framework_version=cfg["framework_versions"]["sklearn"], sagemaker_session=session,
    )
    serving_model = PipelineModel(models=[preprocessor_model, Model(image_uri=xgb_image, model_data=model_data,
                                                                    role=role, sagemaker_session=session)],
                                  role=role, sagemaker_session=session)
    step_register = ModelStep(
        name="RegisterModel",
        step_args=serving_model.register(
            content_types=["text/csv"], response_types=["text/csv"],
            inference_instances=["ml.c5.large", "ml.m5.large", "ml.m5.xlarge"],
            transform_instances=["ml.m5.xlarge", "ml.m5.2xlarge"],
            model_package_group_name=cfg["model_package_group"], approval_status=approval,
            description="TeleConnect churn: sklearn preprocessor + XGBoost",
            model_metrics=ModelMetrics(
                model_statistics=MetricsSource(s3_uri=evaluation_uri, content_type="application/json"),
                bias_post_training=MetricsSource(s3_uri=step_bias.properties.CalculatedBaselineConstraints,
                                                 content_type="application/json"),
                explainability=MetricsSource(s3_uri=step_explain.properties.CalculatedBaselineConstraints,
                                             content_type="application/json"),
            ),
            drift_check_baselines=DriftCheckBaselines(
                model_data_statistics=MetricsSource(
                    s3_uri=step_data_quality.properties.CalculatedBaselineStatistics,
                    content_type="application/json"),
                model_data_constraints=MetricsSource(
                    s3_uri=step_data_quality.properties.CalculatedBaselineConstraints,
                    content_type="application/json"),
            ),
            customer_metadata_properties={
                "git_sha": git_sha,
                "dataset_version": ExecutionVariables.PIPELINE_EXECUTION_ID,
                "algorithm": "xgboost-" + cfg["framework_versions"]["xgboost"],
            },
        ),
    )

    # ---- Quality gate ---------------------------------------------------------------------------
    def metric(path: str):
        return JsonGet(step_name=step_evaluate.name, property_file=evaluation, json_path=path)

    step_fail = FailStep(name="FailOnGate", error_message=Join(on=" ", values=[
        "Quality gate failed: auc", metric("binary_classification_metrics.auc.value"),
        "precision", metric("binary_classification_metrics.precision.value"),
        "recall", metric("binary_classification_metrics.recall.value"),
        "no_regression_ok", metric("gates.no_regression_ok")]))
    step_gate = ConditionStep(
        name="GateKPIs",
        conditions=[
            ConditionGreaterThanOrEqualTo(left=metric("binary_classification_metrics.auc.value"), right=auc_min),
            ConditionGreaterThanOrEqualTo(left=metric("binary_classification_metrics.precision.value"),
                                          right=precision_min),
            ConditionGreaterThanOrEqualTo(left=metric("binary_classification_metrics.recall.value"),
                                          right=recall_min),
            ConditionEquals(left=metric("gates.no_regression_ok"), right=1),
        ],
        if_steps=[step_clarify_model, step_explain, step_bias, step_register],
        else_steps=[step_fail],
    )
    # Baseline + ingest must succeed before anything is registered.
    step_clarify_model.add_depends_on([step_data_quality, step_ingest])

    return Pipeline(
        name=cfg["pipeline_name"],
        parameters=[input_data, processing_type, training_type, approval, git_sha, auc_min, precision_min,
                    recall_min, skip_checks, register_baselines],
        steps=[step_preprocess, step_ingest, step_data_quality, step_train, step_evaluate, step_gate],
        sagemaker_session=session,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true", help="build and print the definition only")
    parser.add_argument("--upsert", action="store_true")
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--git-sha", default=os.environ.get("GITHUB_SHA", "unknown"))
    parser.add_argument("--with-tuning", action="store_true", help="TuningStep instead of TrainingStep")
    args = parser.parse_args()

    cfg = config.project()
    role = cfg["sagemaker_role_arn"] or sagemaker.get_execution_role()
    region = cfg["region"]
    pipeline = get_pipeline(role, cfg["bucket"], region, with_tuning=args.with_tuning)
    definition = json.loads(pipeline.definition())
    if args.validate:
        print(json.dumps({"steps": [s["Name"] for s in definition["Steps"]],
                          "parameters": [p["Name"] for p in definition["Parameters"]]}, indent=2))
    if args.upsert:
        pipeline.upsert(role_arn=role, description="TeleConnect churn retraining pipeline",
                        tags=[{"Key": "project", "Value": cfg["project"]}])
        print(f"upserted {cfg['pipeline_name']}")
    if args.start:
        execution = pipeline.start(parameters={"GitSha": args.git_sha})
        print(execution.arn)


if __name__ == "__main__":
    main()
