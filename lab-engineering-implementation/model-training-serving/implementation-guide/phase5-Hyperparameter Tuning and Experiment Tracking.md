# Phase 5 – Hyperparameter Tuning and Experiment Tracking

## Lab Guide: Optimizing Machine Learning Models Using Amazon SageMaker Hyperparameter Tuning and SageMaker Experiments

**Lab Duration:** **2–2.5 Hours**

---

# Phase Objective

In Phase 4, participants trained multiple baseline machine learning models. Although these models are functional, they may not deliver the best predictive performance.

In this phase, participants will learn how enterprise ML teams optimize models by:

* Running automated hyperparameter tuning jobs
* Tracking every experiment
* Comparing multiple model versions
* Selecting the best model based on objective evaluation metrics
* Preparing the model for final evaluation

Instead of manually trying different parameter combinations, Amazon SageMaker automatically searches for the optimal set of hyperparameters.

---

# Learning Objectives

After completing this phase, participants will be able to:

* Understand the difference between model parameters and hyperparameters.
* Use Amazon SageMaker Hyperparameter Tuning Jobs.
* Configure tuning ranges.
* Choose an optimization strategy.
* Track experiments using SageMaker Experiments.
* Compare multiple training jobs.
* Select the best model for deployment.

---

# Enterprise Architecture

```text
                 Training Dataset
                        │
                        ▼
              SageMaker Training Job
                        │
                        ▼
          Hyperparameter Tuning Job
                        │
      ┌─────────────────┼─────────────────┐
      ▼                 ▼                 ▼
 Training Job 1   Training Job 2   Training Job N
      │                 │                 │
      └─────────────────┼─────────────────┘
                        ▼
             SageMaker Experiments
                        │
                        ▼
                Best Performing Model
                        │
                        ▼
               SageMaker Model Registry
```

---

# What are Hyperparameters?

Hyperparameters are values that control how a machine learning algorithm learns.

Unlike model weights, they are **not learned during training**.

Examples include:

| Hyperparameter       | Purpose                        |
| -------------------- | ------------------------------ |
| Learning Rate        | Controls learning speed        |
| Maximum Tree Depth   | Controls tree complexity       |
| Number of Trees      | Controls model size            |
| Gamma                | Minimum split gain             |
| Minimum Child Weight | Prevents overfitting           |
| Subsample            | Percentage of samples per tree |

---

# Why Hyperparameter Tuning?

Without tuning:

```text
Default Parameters
        │
        ▼
Average Accuracy
```

With tuning:

```text
Many Parameter Combinations
        │
        ▼
Automatic Search
        │
        ▼
Best Accuracy
```

Benefits include:

* Improved accuracy
* Reduced overfitting
* Better generalization
* Automated optimization
* Reduced manual effort

---

# Input

From Phase 4:

```text
Training Dataset

Baseline Models

Training Scripts
```

---

# Output

```text
Optimized Model

Experiment History

Training Metrics

Best Hyperparameters
```

---

# Task 1 – Review the Baseline Model

Review the metrics obtained in Phase 4.

Example:

| Metric    | Value |
| --------- | ----- |
| Accuracy  | 89%   |
| Precision | 84%   |
| Recall    | 78%   |
| ROC AUC   | 0.91  |

Discussion:

* Can we improve Recall?
* Can we reduce False Negatives?
* Which metric is most important for churn prediction?

---

# Task 2 – Understand the Optimization Goal

Business Requirement

Missing a customer who is likely to churn is expensive.

Therefore, optimize for:

* ROC AUC
* Recall
* F1 Score

rather than Accuracy alone.

---

# Task 3 – Create a SageMaker Experiment

Experiments allow tracking every model training run.

```python
from sagemaker.experiments.run import Run

run = Run(
    experiment_name="customer-churn-experiment",
    run_name="xgboost-baseline"
)
```

Discussion

Why use Experiments?

* Reproducibility
* Governance
* Model lineage
* Team collaboration
* Auditability

---

# Task 4 – Configure Hyperparameter Ranges

For XGBoost:

```python
from sagemaker.tuner import (
    IntegerParameter,
    ContinuousParameter
)

hyperparameter_ranges = {

    "max_depth": IntegerParameter(3,10),

    "eta": ContinuousParameter(0.01,0.30),

    "gamma": ContinuousParameter(0,10),

    "min_child_weight": IntegerParameter(1,10),

    "subsample": ContinuousParameter(0.5,1.0),

    "num_round": IntegerParameter(100,500)
}
```

---

Discussion

Explain every parameter.

| Parameter        | Effect                                            |
| ---------------- | ------------------------------------------------- |
| max_depth        | Larger → more complex trees                       |
| eta              | Smaller → slower but often more accurate learning |
| gamma            | Larger → more conservative trees                  |
| min_child_weight | Prevents overfitting                              |
| subsample        | Improves generalization                           |
| num_round        | Number of boosting rounds                         |

---

# Task 5 – Define the Objective Metric

Choose the metric to optimize.

```python
objective_metric_name = "validation:auc"
```

Alternative metrics:

* validation:error
* validation:logloss
* validation:auc

Discussion

Why is AUC preferred?

Because churn datasets are often imbalanced.

---

# Task 6 – Configure the Hyperparameter Tuner

```python
from sagemaker.tuner import HyperparameterTuner

tuner = HyperparameterTuner(

    estimator=xgb,

    objective_metric_name="validation:auc",

    hyperparameter_ranges=hyperparameter_ranges,

    objective_type="Maximize",

    max_jobs=20,

    max_parallel_jobs=4
)
```

---

Discussion

Explain:

| Parameter         | Meaning                      |
| ----------------- | ---------------------------- |
| max_jobs          | Total training jobs          |
| max_parallel_jobs | Jobs executed simultaneously |

---

# Task 7 – Launch the Tuning Job

```python
tuner.fit({

    "train": train_path,

    "validation": validation_path

})
```

Expected Result

SageMaker launches:

```
20 Training Jobs
```

automatically.

---

# Task 8 – Monitor the Tuning Job

Navigate to:

```
Amazon SageMaker

↓

Hyperparameter Tuning Jobs
```

Observe:

* Running Jobs
* Best Job
* Current Metric
* Hyperparameters

Discussion

How does SageMaker determine the next parameter combination?

Introduce:

* Bayesian Optimization
* Random Search
* Grid Search

Explain why Bayesian Optimization is the default and typically more efficient.

---

# Task 9 – Review the Best Model

Retrieve:

```python
best_estimator = tuner.best_estimator()
```

Display:

```python
print(best_estimator.hyperparameters())
```

Expected Output

```
max_depth = 5

eta = 0.08

gamma = 2

num_round = 320

subsample = 0.78
```

---

# Task 10 – Compare Experiments

Navigate:

```
SageMaker Studio

↓

Experiments
```

Compare:

* Training time
* Hyperparameters
* Metrics
* Artifacts

Discussion

Which experiment performed best?

---

# Task 11 – Compare Baseline vs Optimized Model

Create a comparison table.

| Metric    | Baseline | Optimized |
| --------- | -------- | --------- |
| Accuracy  | 89%      | 92%       |
| Precision | 84%      | 89%       |
| Recall    | 78%      | 86%       |
| F1 Score  | 81%      | 88%       |
| ROC AUC   | 0.91     | 0.95      |

Discussion

Which metric improved the most?

---

# Task 12 – Save the Best Model

The best estimator automatically stores artifacts in Amazon S3.

Verify:

```
models/

best-model/

model.tar.gz
```

Discussion

Why keep every model version?

* Rollback
* Audit
* Comparison
* Regulatory compliance

---

# Task 13 – Document Experiment Results

Create a summary table.

| Run    | Algorithm | AUC  | Recall | Training Time | Rank |
| ------ | --------- | ---- | ------ | ------------- | ---- |
| Run 1  | XGBoost   | 0.91 | 78%    | 3 min         | 5    |
| Run 7  | XGBoost   | 0.94 | 84%    | 4 min         | 2    |
| Run 15 | XGBoost   | 0.95 | 86%    | 5 min         | 1    |

---

# Task 14 – Review CloudWatch Logs

Navigate:

```
CloudWatch

↓

Logs

↓

Training Jobs
```

Observe:

* Metric progression
* Job duration
* Resource utilization
* Warnings

Discussion

Why monitor every tuning job?

---

# Best Practices

* Start with broad hyperparameter ranges, then narrow them.
* Optimize the metric that aligns with the business objective (e.g., Recall or AUC for churn prediction).
* Use validation data only for tuning; keep the test dataset untouched until final evaluation.
* Limit the number of parallel jobs to control AWS costs.
* Track every experiment for reproducibility and governance.
* Save experiment metadata, including code version and dataset version.

---

# Deliverables

Participants should submit:

1. Hyperparameter tuning notebook.
2. SageMaker Hyperparameter Tuning Job screenshot.
3. SageMaker Experiments screenshot.
4. Comparison table of baseline and tuned models.
5. Best hyperparameter configuration.
6. Best model artifact location in Amazon S3.
7. Training logs from CloudWatch.

---

# Validation Checklist

| Validation                       | Expected Result |
| -------------------------------- | --------------- |
| Experiment created               | ✓               |
| Hyperparameter ranges configured | ✓               |
| Tuning job completed             | ✓               |
| Multiple training jobs executed  | ✓               |
| Best estimator identified        | ✓               |
| Best model saved                 | ✓               |
| Experiments recorded             | ✓               |
| CloudWatch logs available        | ✓               |

---

# Discussion Questions

1. What is the difference between a model parameter and a hyperparameter?
2. Why is Bayesian Optimization generally preferred over Grid Search?
3. Why should the test dataset not be used during tuning?
4. Why might Recall be more important than Accuracy in churn prediction?
5. How do SageMaker Experiments support collaboration and regulatory compliance?
6. What trade-offs exist between model performance, training time, and infrastructure cost?

---

# Transition to Phase 6

By the end of this phase, participants have selected the best-performing model and documented the optimization process. In **Phase 6 – Model Evaluation and Explainability**, they will:

* Evaluate the tuned model on the untouched test dataset.
* Generate confusion matrices, ROC and Precision–Recall curves.
* Measure Accuracy, Precision, Recall, F1 Score, and ROC AUC.
* Use **Amazon SageMaker Clarify** to analyze feature importance, SHAP values, bias, and explainability.
* Decide whether the model meets the business success criteria and is ready for registration and deployment.
