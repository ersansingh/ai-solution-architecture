import json

import pytest

from churn.deploy import export_model as em


class FakeBlob:
    def __init__(self, store, name):
        self.store, self.name = store, name

    def exists(self):
        return self.name in self.store

    def download_blob(self):
        data = self.store[self.name]

        class _D:
            def readall(self):
                return data

        return _D()

    def upload_blob(self, data, overwrite=False):
        if not overwrite and self.name in self.store:
            raise RuntimeError("exists")
        self.store[self.name] = data if isinstance(data, bytes) else data.read()


class FakeContainer:
    def __init__(self, exists=True):
        self.store = {}
        self._exists = exists

    def exists(self):
        return self._exists

    def get_blob_client(self, name):
        return FakeBlob(self.store, name)

    def upload_blob(self, name, data, overwrite=False):
        FakeBlob(self.store, name).upload_blob(data, overwrite)


def model_dir(tmp_path, bst=b"booster"):
    d = tmp_path / "model"
    d.mkdir()
    (d / "model.bst").write_bytes(bst)
    (d / "calibrator.json").write_text('{"calibrator": {}}')
    (d / "MLmodel").write_text("flavors: {}")
    return d


def test_uri_and_prefix_avoid_version_prefix_collisions():
    prefix = em.blob_prefix("churn-lightgbm", "7")
    assert prefix == "churn-lightgbm/7/artifacts"
    assert not em.blob_prefix("churn-lightgbm", "70").startswith(prefix)
    uri = em.storage_uri("stlakechurnprodab12c", "models", prefix)
    assert uri == "https://stlakechurnprodab12c.blob.core.windows.net/models/" + prefix
    # matches KServe's _AZURE_BLOB_RE
    assert uri.startswith("https://") and ".blob.core.windows.net/" in uri
    with pytest.raises(ValueError):
        em.storage_uri("Bad_Account", "models", prefix)
    with pytest.raises(ValueError):
        em.blob_prefix("a/b", "1")


def test_missing_serving_files_rejected(tmp_path):
    d = tmp_path / "m"
    d.mkdir()
    (d / "model.bst").write_bytes(b"x")
    with pytest.raises(ValueError, match="calibrator.json"):
        em.collect_files(d)


def test_export_uploads_files_then_manifest_and_is_idempotent(tmp_path):
    c = FakeContainer()
    d = model_dir(tmp_path)
    prefix = em.blob_prefix("churn-lightgbm", "3")
    assert em.export(c, d, prefix, {"model_version": "3"}) == "uploaded"
    assert set(c.store) == {
        f"{prefix}/model.bst",
        f"{prefix}/calibrator.json",
        f"{prefix}/MLmodel",
        f"{prefix}/manifest.json",
    }
    manifest = json.loads(c.store[f"{prefix}/manifest.json"])
    assert set(manifest["files"]) == {"model.bst", "calibrator.json", "MLmodel"}
    assert em.export(c, d, prefix, {"model_version": "3"}) == "unchanged"
    (d / "model.bst").write_bytes(b"different")
    with pytest.raises(ValueError, match="immutable"):
        em.export(c, d, prefix, {})


def test_main_writes_github_output(tmp_path, monkeypatch):
    c = FakeContainer()
    out = tmp_path / "gh_out"
    d = model_dir(tmp_path)
    code = em.main(
        [
            "--model-name",
            "churn-lightgbm",
            "--model-version",
            "5",
            "--account",
            "stlakechurnprod1",
            "--github-output",
            str(out),
        ],
        downloader=lambda name, ver, dst: d,
        container_factory=lambda account, container: c,
    )
    assert code == 0
    text = out.read_text()
    assert (
        "storage_uri=https://stlakechurnprod1.blob.core.windows.net/models/"
        "churn-lightgbm/5/artifacts\n"
    ) in text
    assert "model_version=5" in text


def test_main_fails_without_container(tmp_path):
    code = em.main(
        ["--model-name", "m", "--model-version", "1", "--account", "acct1", "--local-dir", "."],
        container_factory=lambda a, c: FakeContainer(exists=False),
    )
    assert code == 1
