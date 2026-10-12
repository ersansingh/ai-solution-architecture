"""Customer churn prediction platform: CI, evaluation-gate and rollout tooling.

Subpackages are invoked as CLIs from ``pipelines/churn-mlops-pipeline.yml``:

* ``churn.data_contracts.run``      - data-contract validation of CI fixtures
* ``churn.evaluation.gates``        - champion/challenger evaluation gates
* ``churn.deploy.shadow_analysis``  - shadow (mirrored traffic) analysis
* ``churn.deploy.canary_analysis``  - canary vs stable analysis between steps
* ``churn.deploy.smoke_test``       - post-promotion smoke test through APIM
"""

__version__ = "1.0.0"
