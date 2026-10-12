import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in ("src", "services/churn-api", "services/model-server", "deployment/lambdas", "deployment"):
    sys.path.insert(0, str(ROOT / path))
os.environ.setdefault("CHURN_CONFIG_DIR", str(ROOT / "config"))
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
