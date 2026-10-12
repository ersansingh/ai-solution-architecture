"""Keeps pipelines/churn-mlops-pipeline.yml coherent with the repository.

Every ``python -m churn...`` module, every referenced file and every
``envsubst`` manifest must exist, parse, and accept the CLI flags the pipeline
passes.
"""

import importlib
import json
import re
import shlex
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "pipelines/churn-mlops-pipeline.yml"
ENVSUBST_VARS = {
    "ISVC_NAME": "churn-lgbm",
    "KSERVE_NAMESPACE": "churn-serving",
    "STORAGE_URI": (
        "https://stlakechurnprodab12c.blob.core.windows.net/models/churn-lightgbm/3/artifacts"
    ),
    "MODEL_VERSION": "3",
    "SHADOW_STARTED": "2026-10-11T03:00:00Z",
    "ACR_LOGIN": "acrchurnprod.azurecr.io",
    "IMAGE_NAME": "churn/kserve-transformer",
    "IMAGE_TAG": "abc123",
    "SERVING_IDENTITY_CLIENT_ID": "00000000-0000-0000-0000-000000000000",
    "LAKE_STORAGE_ACCOUNT": "stlakechurnprod",
    "KEY_VAULT_NAME": "kv-churnprodab12c",
    "AZURE_TENANT_ID": "11111111-1111-1111-1111-111111111111",
    "ISTIO_INGRESS_GATEWAY": "aks-istio-ingress/churn-api-gateway",
    "CHURN_API_INGRESS_HOST": "churn-scoring.internal.example.com",
}


def envsubst(text, **extra):
    """Mimic envsubst for ${VAR} / $VAR; unknown variables are an error."""
    values = {**ENVSUBST_VARS, **extra}

    def sub(m):
        name = m.group(1) or m.group(2)
        assert name in values, f"unset variable {name}"
        return values[name]

    return re.sub(r"\$\{(\w+)\}|\$([A-Za-z_]\w*)", sub, text)


def pipeline_text():
    return PIPELINE.read_text()


def run_scripts():
    doc = yaml.safe_load(pipeline_text())
    for job in doc["jobs"].values():
        for step in job.get("steps", []):
            if "run" in step:
                yield step["run"]


def module_invocations():
    """Yield (module, argv) for every `python -m churn.*` call in the pipeline."""
    for script in run_scripts():
        joined = re.sub(r"\\\n\s*", " ", script)
        for line in joined.splitlines():
            m = re.search(r"python -m (churn\.[\w.]+)(.*)", line)
            if m:
                yield m.group(1), shlex.split(m.group(2))


def test_pipeline_parses_and_runs_from_project_dir():
    doc = yaml.safe_load(pipeline_text())
    workdir = doc["defaults"]["run"]["working-directory"]
    assert (ROOT.parents[1] / workdir).resolve() == ROOT


@pytest.mark.parametrize("module", sorted({m for m, _ in module_invocations()}))
def test_modules_exist(module):
    assert importlib.import_module(module)


def test_cli_flags_match_parsers():
    seen = 0
    for module, argv in module_invocations():
        mod = importlib.import_module(module)
        parser = mod.build_parser()
        known = {a for action in parser._actions for a in action.option_strings}
        flags = {a for a in argv if a.startswith("--")}
        assert flags <= known, (module, flags - known)
        seen += 1
    assert seen >= 6


@pytest.mark.parametrize(
    "path",
    [
        "requirements-dev.txt",
        "serving/Dockerfile",
        "serving/requirements-deploy.txt",
        "serving/k8s/inferenceservice-shadow.yaml",
        "serving/k8s/virtualservice-mirror.yaml",
        "pipelines/aml/churn-training-pipeline.yml",
        "data_contracts/gold_customer_features.json",
        "data_contracts/silver_billing.json",
        "tests/fixtures/contract_samples",
        "tests/leakage",
        "tests/fixtures/smoke_customer_ids.txt",
        "serving/k8s/secretproviderclass-redis.yaml",
        "serving/k8s/remove-shadow.sh",
        "pipelines/aml/scripts/ensure-datastores.sh",
        "features/feature_store.yaml",
    ],
)
def test_referenced_paths_exist(path):
    assert path in pipeline_text() or path.startswith("tests/fixtures/smoke")
    assert (ROOT / path).exists()


@pytest.mark.parametrize("manifest", sorted((ROOT / "serving/k8s").glob("*.yaml")))
def test_k8s_manifests_render(manifest):
    rendered = envsubst(manifest.read_text())
    docs = [d for d in yaml.safe_load_all(rendered) if d]
    assert docs and all({"apiVersion", "kind", "metadata"} <= set(d) for d in docs)


def test_canary_json_patch_paths_exist_in_champion_isvc():
    isvc = yaml.safe_load(envsubst((ROOT / "serving/k8s/inferenceservice.yaml").read_text()))
    script = next(s for s in run_scripts() if "--type json" in s)
    raw = script[script.index('-p "') + 4 : script.index(']"') + 1].replace('\\"', '"')
    ops = json.loads(envsubst(raw, ACR_NAME="acr"))
    for op in ops:
        if op["op"] != "replace":
            continue
        node = isvc
        for part in op["path"].strip("/").split("/"):
            node = node[int(part)] if isinstance(node, list) else node[part]
    container = isvc["spec"]["transformer"]["containers"][0]
    assert container["name"] == "kserve-container"
    assert container["env"][0]["name"] == "STORAGE_URI"


def test_aml_pipeline_components_and_outputs():
    aml = ROOT / "pipelines/aml"
    job = yaml.safe_load((aml / "churn-training-pipeline.yml").read_text())
    assert job["type"] == "pipeline"
    assert "snapshot_date" in job["inputs"]
    assert "evaluation_report" in job["outputs"]
    computes = {j.get("compute", job["settings"]["default_compute"]) for j in job["jobs"].values()}
    assert computes == {"azureml:cpu-training", "azureml:cpu-tuning-spot"}
    for name, step in job["jobs"].items():
        comp_path = aml / step["component"]
        comp = yaml.safe_load(comp_path.read_text())
        assert set(step.get("inputs", {})) <= set(comp["inputs"]), name
        assert set(step.get("outputs", {})) <= set(comp["outputs"]), name
        assert (comp_path.parent / comp["code"]).is_dir()
        assert (comp_path.parent / comp["environment"]["conda_file"]).is_file()
        script = comp["command"].split()[1]
        assert (comp_path.parent / comp["code"] / script).is_file()
        flags = set(re.findall(r"--[\w-]+", comp["command"]))
        source = (comp_path.parent / comp["code"] / script).read_text()
        assert all(f'"{f}"' in source for f in flags), name


# ---------------------------------------------------------------------------
# Deployment prerequisites (ai-solution-architecture-6p0)
# ---------------------------------------------------------------------------
def pipeline_doc():
    return yaml.safe_load(pipeline_text())


def job_scripts(job):
    return "\n".join(s.get("run", "") for s in pipeline_doc()["jobs"][job]["steps"])


def k8s(name):
    return [d for d in yaml.safe_load_all(envsubst((ROOT / "serving/k8s" / name).read_text())) if d]


def test_github_configuration_documented():
    text = pipeline_text()
    readme = (ROOT / "pipelines/README.md").read_text()
    names = set(re.findall(r"\b(?:secrets|vars)\.([A-Z][A-Z0-9_]+)", text))
    envs = {
        j["environment"] if isinstance(j["environment"], str) else j["environment"]["name"]
        for j in pipeline_doc()["jobs"].values()
        if "environment" in j
    }
    assert "CHURN_API_SCOPE" in names
    missing = sorted(n for n in names | envs if f"`{n}`" not in readme)
    assert not missing, f"undocumented in pipelines/README.md: {missing}"
    assert "10080" in readme  # shadow-soak wait timer


def test_weekly_retrain_cron_matches_design_sunday():
    doc = pipeline_doc()
    triggers = doc.get("on", doc.get(True))  # PyYAML parses bare `on` as True
    crons = [c["cron"] for c in triggers["schedule"]]
    assert crons == ["0 2 * * 0"]
    assert "Sunday 02:00" in (ROOT / "system-design.md").read_text()


def test_model_exported_to_blob_before_kserve():
    jobs = pipeline_doc()["jobs"]
    reg = jobs["register-model"]
    assert "steps.export.outputs.storage_uri" in reg["outputs"]["storage_uri"]
    assert "python -m churn.deploy.export_model" in job_scripts("register-model")
    for job in ("deploy-shadow", "deploy-canary"):
        assert jobs[job]["env"]["STORAGE_URI"] == "${{ needs.register-model.outputs.storage_uri }}"
    assert "azureml://" not in pipeline_text().split("register-model:")[1]
    kserve_blob_re = r"https://(.+?).blob.core.windows.net/(.+)"  # kserve.storage
    for manifest in ("inferenceservice.yaml", "inferenceservice-shadow.yaml"):
        isvc = k8s(manifest)[0]
        uri = isvc["spec"]["predictor"]["model"]["storageUri"]
        assert re.match(kserve_blob_re, uri) and uri.endswith("/artifacts")
        env = isvc["spec"]["transformer"]["containers"][0]["env"]
        assert env[0] == {"name": "STORAGE_URI", "value": uri}
        assert isvc["spec"]["predictor"]["labels"]["azure.workload.identity/use"] == "true"


def test_aml_datastores_identity_based_and_match_terraform():
    aml = ROOT / "pipelines/aml"
    stores = {}
    for f in (aml / "datastores").glob("*.yml"):
        d = yaml.safe_load(f.read_text())
        assert d["type"] == "azure_data_lake_gen2"
        assert "credentials" not in d, f"{f.name} must be identity-based"
        stores[d["name"]] = d
    used = set(
        re.findall(
            r"azureml://datastores/(\w+)/", (aml / "churn-training-pipeline.yml").read_text()
        )
    )
    assert used and used <= set(stores)
    tf_vars = (ROOT / "terraform/variables.tf").read_text()
    lake_block = tf_vars[tf_vars.index('variable "lake_containers"') :]
    lake_default = re.search(r"default\s*=\s*\[([^\]]*)\]", lake_block).group(1)
    containers = set(re.findall(r'"([\w-]+)"', lake_default))
    assert {d["filesystem"] for d in stores.values()} <= containers
    assert "ensure-datastores.sh" in job_scripts("ct-train")
    script = (aml / "scripts/ensure-datastores.sh").read_text()
    assert "--set account_name=" in script and "az ml datastore create" in script
    job = yaml.safe_load((aml / "churn-training-pipeline.yml").read_text())
    assert job["jobs"]["prepare_data"]["identity"]["type"] == "managed"


def test_redis_secret_synced_by_csi_and_referenced_by_isvcs():
    spc, sync = k8s("secretproviderclass-redis.yaml")
    assert spc["kind"] == "SecretProviderClass" and spc["spec"]["provider"] == "azure"
    assert spc["spec"]["parameters"]["usePodIdentity"] == "false"
    synced = spc["spec"]["secretObjects"][0]
    kv_object = synced["data"][0]["objectName"]
    assert kv_object in spc["spec"]["parameters"]["objects"]
    assert kv_object == pipeline_doc()["env"]["REDIS_KV_SECRET"]
    vol = sync["spec"]["template"]["spec"]["volumes"][0]["csi"]
    assert vol["volumeAttributes"]["secretProviderClass"] == spc["metadata"]["name"]
    assert sync["spec"]["template"]["spec"]["serviceAccountName"] == "churn-kserve-sa"
    for manifest in ("inferenceservice.yaml", "inferenceservice-shadow.yaml"):
        env = k8s(manifest)[0]["spec"]["transformer"]["containers"][0]["env"]
        ref = next(e for e in env if e["name"] == "REDIS_CONNECTION_STRING")["valueFrom"]
        assert ref["secretKeyRef"] == {
            "name": synced["secretName"],
            "key": synced["data"][0]["key"],
        }
    assert "secretproviderclass-redis.yaml" in job_scripts("deploy-shadow")


def test_mirror_covers_ingress_gateway_and_mesh():
    svc, mirror = k8s("virtualservice-mirror.yaml")
    (api,) = k8s("virtualservice-api.yaml")
    assert mirror["metadata"]["name"] == api["metadata"]["name"]  # same object, toggled
    assert set(mirror["spec"]["gateways"]) == {"mesh", ENVSUBST_VARS["ISTIO_INGRESS_GATEWAY"]}
    assert ENVSUBST_VARS["CHURN_API_INGRESS_HOST"] in mirror["spec"]["hosts"]
    assert set(api["spec"]["hosts"]) <= set(mirror["spec"]["hosts"])
    assert "mirror" not in api["spec"]["http"][0]
    target = mirror["spec"]["http"][0]["mirror"]["host"]
    assert target.startswith(svc["metadata"]["name"] + ".")
    remove = (ROOT / "serving/k8s/remove-shadow.sh").read_text()
    assert "virtualservice-api.yaml" in remove


def test_shadow_soak_is_seven_days_before_canary():
    jobs = pipeline_doc()["jobs"]
    soak = jobs["shadow-analysis"]
    assert soak["environment"] == "shadow-soak"
    assert "deploy-shadow" in soak["needs"]
    assert "shadow-analysis" in jobs["deploy-canary"]["needs"]
    assert pipeline_doc()["env"]["SHADOW_SOAK_DAYS"] == "7"
    script = job_scripts("shadow-analysis")
    assert "--lookback" in script and "remove-shadow.sh" in script
    assert "--window 2h" not in pipeline_text()
    isvc = k8s("inferenceservice-shadow.yaml")[0]
    assert "churn.ai/shadow-started" in isvc["metadata"]["annotations"]
    assert "concurrency" not in pipeline_doc()  # a 7-day run must not block CI


def test_smoke_test_uses_server_side_timing_for_slo():
    script = job_scripts("deploy-canary")
    joined = re.sub(r"\\\n\s*", " ", script)
    line = next(ln for ln in joined.splitlines() if "churn.deploy.smoke_test" in ln)
    assert '--max-server-p99-ms "$MAX_P99_LATENCY_MS"' in line
    assert '--max-client-p99-ms "$MAX_P99_APIM_MS"' in line
    env = pipeline_doc()["env"]
    assert float(env["MAX_P99_APIM_MS"]) > float(env["MAX_P99_LATENCY_MS"])


def test_single_feast_config_baked_into_image():
    assert not (ROOT / "serving/feature_repo").exists()
    dockerfile = (ROOT / "serving/Dockerfile").read_text()
    assert "COPY --from=features feature_store.yaml" in dockerfile
    build = next(
        s
        for s in pipeline_doc()["jobs"]["build-and-scan"]["steps"]
        if s.get("uses", "").startswith("docker/build-push-action")
    )
    assert "features=${{ env.APP_DIR }}/features" in build["with"]["build-contexts"]
    apply = job_scripts("feature-store-apply")
    assert "feast apply" in apply and "repo/feature_store.yaml" in apply
    assert "feature-store-apply" in pipeline_doc()["jobs"]["ct-train"]["needs"]
