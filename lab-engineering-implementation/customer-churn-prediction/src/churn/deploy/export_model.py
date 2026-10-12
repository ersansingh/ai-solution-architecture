"""Export a registered MLflow model version to Blob Storage for KServe.

KServe's storage initializer (predictor) and ``kserve.Storage`` (transformer)
cannot resolve ``azureml://`` / ``models:/`` URIs. They do support
``https://<account>.blob.core.windows.net/<container>/<prefix>`` and
authenticate with ``DefaultAzureCredential`` whenever ``AZURE_CLIENT_ID`` is
set, which the AKS workload identity webhook injects into pods labelled
``azure.workload.identity/use: "true"`` (``churn-kserve-sa``, Storage Blob Data
Reader on the lake account in terraform).

This module downloads ``models:/<name>/<version>`` from the Azure ML MLflow
registry, checks that the serving files exist (``model.bst`` for MLServer
LightGBM, ``calibrator.json`` for the transformer), uploads every file to::

    https://<account>.blob.core.windows.net/<container>/<name>/<version>/artifacts/

and writes ``manifest.json`` (sha256 per file, lineage) *last* as the commit
marker. The ``/artifacts`` leaf keeps version prefixes from colliding: KServe
lists blobs by raw prefix, so ``<name>/7`` would also match ``<name>/70/...``.

Re-running for a version that already has a manifest is a no-op when the
hashes match and an error when they differ (exported versions are immutable).

Writes ``storage_uri=...`` and ``model_version=...`` to ``--github-output``.
Exit codes: 0 = exported (or already exported), 1 = error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

REQUIRED_FILES = ("model.bst", "calibrator.json")
MANIFEST = "manifest.json"
_ACCOUNT = re.compile(r"^[a-z0-9]{3,24}$")
_CONTAINER = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])$")


def blob_prefix(model_name: str, version: str) -> str:
    if not model_name or "/" in model_name or not str(version).strip():
        raise ValueError(f"invalid model name/version: {model_name!r} {version!r}")
    return f"{model_name}/{version}/artifacts"


def storage_uri(account: str, container: str, prefix: str) -> str:
    if not _ACCOUNT.match(account):
        raise ValueError(f"invalid storage account name {account!r}")
    if not _CONTAINER.match(container):
        raise ValueError(f"invalid container name {container!r}")
    return f"https://{account}.blob.core.windows.net/{container}/{prefix}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(local_dir: Path) -> dict[str, Path]:
    """Relative POSIX path -> local file, after checking the serving files exist."""
    files = {
        p.relative_to(local_dir).as_posix(): p
        for p in sorted(local_dir.rglob("*"))
        if p.is_file() and p.name != MANIFEST
    }
    missing = [f for f in REQUIRED_FILES if f not in files]
    if missing:
        raise ValueError(f"model artifacts missing {missing} in {local_dir}")
    return files


def build_manifest(files: dict[str, Path], meta: dict[str, Any]) -> dict[str, Any]:
    return {**meta, "files": {rel: sha256(path) for rel, path in sorted(files.items())}}


def export(
    container_client: Any,
    local_dir: Path,
    prefix: str,
    meta: dict[str, Any],
) -> str:
    """Upload ``local_dir`` under ``prefix``; returns 'uploaded' or 'unchanged'."""
    files = collect_files(local_dir)
    manifest = build_manifest(files, meta)
    marker = container_client.get_blob_client(f"{prefix}/{MANIFEST}")
    if marker.exists():
        existing = json.loads(marker.download_blob().readall())
        if existing.get("files") != manifest["files"]:
            raise ValueError(f"{prefix} already exported with different content (immutable)")
        return "unchanged"
    # No manifest: nothing or a partial upload from a failed run -> (re)upload all.
    for rel, path in files.items():
        with open(path, "rb") as fh:
            container_client.upload_blob(f"{prefix}/{rel}", fh, overwrite=True)
    marker.upload_blob(json.dumps(manifest, indent=2).encode(), overwrite=False)
    return "uploaded"


def mlflow_download(model_name: str, version: str, dst: str) -> Path:  # pragma: no cover
    import mlflow

    return Path(
        mlflow.artifacts.download_artifacts(
            artifact_uri=f"models:/{model_name}/{version}", dst_path=dst
        )
    )


def blob_container(account: str, container: str) -> Any:  # pragma: no cover
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient

    service = BlobServiceClient(
        f"https://{account}.blob.core.windows.net", credential=DefaultAzureCredential()
    )
    return service.get_container_client(container)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m churn.deploy.export_model", description=__doc__)
    p.add_argument("--model-name", required=True)
    p.add_argument("--model-version", required=True)
    p.add_argument("--account", required=True, help="lake storage account name")
    p.add_argument("--container", default="models")
    p.add_argument("--local-dir", help="use already-downloaded artifacts (skip MLflow)")
    p.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    return p


def main(
    argv: list[str] | None = None,
    downloader: Callable[[str, str, str], Path] = mlflow_download,
    container_factory: Callable[[str, str], Any] = blob_container,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        prefix = blob_prefix(args.model_name, args.model_version)
        uri = storage_uri(args.account, args.container, prefix)
        container = container_factory(args.account, args.container)
        if not container.exists():
            raise ValueError(
                f"container {args.container!r} not found on {args.account}; add it to "
                "terraform var.lake_containers (see pipelines/README.md)"
            )
        meta = {
            "model_name": args.model_name,
            "model_version": str(args.model_version),
            "git_sha": os.environ.get("GITHUB_SHA", "unknown"),
            "pipeline_run": os.environ.get("GITHUB_RUN_ID", "unknown"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            local = (
                Path(args.local_dir)
                if args.local_dir
                else downloader(args.model_name, args.model_version, tmp)
            )
            status = export(container, local, prefix, meta)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"ERROR: model export failed: {exc}", file=sys.stderr)
        return 1
    print(f"{status}: {uri}")
    if args.github_output:
        with open(args.github_output, "a") as fh:
            fh.write(f"storage_uri={uri}\nmodel_version={args.model_version}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
