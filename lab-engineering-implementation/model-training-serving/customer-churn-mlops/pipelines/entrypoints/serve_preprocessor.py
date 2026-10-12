"""Bundle-root entry point for the scikit-learn serving container (PipelineModel container 1)."""
from churn.preprocessor_serve import input_fn, model_fn, output_fn, predict_fn  # noqa: F401
