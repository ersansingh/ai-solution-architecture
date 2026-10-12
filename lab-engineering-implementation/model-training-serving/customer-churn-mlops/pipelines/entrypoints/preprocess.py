"""Bundle-root entry point so `churn` is importable inside the SageMaker container."""
from churn.jobs.preprocess import main

if __name__ == "__main__":
    main()
