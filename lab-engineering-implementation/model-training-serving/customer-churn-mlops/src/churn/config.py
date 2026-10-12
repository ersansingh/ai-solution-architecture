"""Load project configuration from config/*.yaml with environment overrides."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml

# config/ lives at the project root; inside SageMaker containers it is shipped next to the package.
_CANDIDATES = [
    Path(os.environ.get("CHURN_CONFIG_DIR", "")),
    Path(__file__).resolve().parents[2] / "config",  # repo checkout: <root>/src/churn
    Path(__file__).resolve().parents[1] / "config",  # SageMaker source bundle: <bundle>/churn
    Path("/opt/ml/code/config"),
]


def config_dir() -> Path:
    for candidate in _CANDIDATES:
        if str(candidate) and (candidate / "features.yaml").exists():
            return candidate
    raise FileNotFoundError("config/features.yaml not found; set CHURN_CONFIG_DIR")


def _load_yaml(name: str) -> Dict[str, Any]:
    with open(config_dir() / name) as fh:
        return yaml.safe_load(fh)


@lru_cache(maxsize=None)
def features() -> Dict[str, Any]:
    return _load_yaml("features.yaml")


@lru_cache(maxsize=None)
def quality_gates() -> Dict[str, Any]:
    return _load_yaml("quality_gates.yaml")


@lru_cache(maxsize=None)
def best_hparams() -> Dict[str, str]:
    with open(config_dir() / "best_hparams.json") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def project() -> Dict[str, Any]:
    cfg = _load_yaml("project.yaml")
    for key, value in list(cfg.items()):
        env_value = os.environ.get(f"CHURN_{key.upper()}")
        if env_value is not None and not isinstance(value, dict):
            cfg[key] = env_value
    return cfg


def categorical_columns() -> list:
    return list(features()["categorical"].keys())


def numeric_columns() -> list:
    return list(features()["numeric"])


def model_input_columns() -> list:
    """Order of the raw feature vector sent to the endpoint (CSV, no header)."""
    return numeric_columns() + categorical_columns()


def s3_uri(prefix_key: str, *parts: str) -> str:
    cfg = project()
    path = "/".join([cfg["prefixes"][prefix_key], *[p.strip("/") for p in parts if p]])
    return f"s3://{cfg['bucket']}/{path}"
