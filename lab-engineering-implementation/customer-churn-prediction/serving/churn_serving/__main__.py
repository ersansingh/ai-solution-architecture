"""Entrypoint: ``python -m churn_serving``.

KServe injects ``--model_name``, ``--predictor_host`` and ``--http_port`` into
custom transformer containers.
"""

from __future__ import annotations

import argparse

import kserve

from churn_serving.timing import install as install_server_timing
from churn_serving.transformer import ChurnTransformer

parser = argparse.ArgumentParser(parents=[kserve.model_server.parser])
parser.add_argument("--predictor_host", required=True, help="set by KServe")


def main() -> None:
    args, _ = parser.parse_known_args()
    model = ChurnTransformer(args.model_name, args.predictor_host)
    model.load()
    install_server_timing()  # x-churn-server-time-ms on every response
    kserve.ModelServer().start([model])


if __name__ == "__main__":
    main()
