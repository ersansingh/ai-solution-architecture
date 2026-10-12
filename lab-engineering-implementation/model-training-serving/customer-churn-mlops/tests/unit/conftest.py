import pytest

from churn.data.generate_synthetic import generate
from churn.jobs import local_train


@pytest.fixture(scope="session")
def trained(tmp_path_factory):
    """Small end-to-end local run shared by the model-server and integration-style unit tests."""
    work = tmp_path_factory.mktemp("work")
    generate(20_000, str(work / "data"), "2026-10-01", seed=11)
    summary = local_train.run(20_000, str(work))
    return work, summary
