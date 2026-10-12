"""Bundle-root entry point so `churn` is importable inside the SageMaker container."""
from churn.jobs.ingest_features import main

if __name__ == "__main__":
    main()
