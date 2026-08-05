# Phase 6 – Model Evaluation, Explainability, and Bias Detection

## Lab Guide: Evaluating the Best Model Using Amazon SageMaker Clarify

**Lab Duration:** **2.5–3 Hours**

---

# Phase Objective

In Phase 5, participants optimized their machine learning models using **Amazon SageMaker Hyperparameter Tuning Jobs** and identified the best-performing model.

However, **high accuracy alone is not enough** to deploy a model into production.

Enterprise AI systems must answer critical questions:

* Is the model accurate enough?
* Can business users trust its predictions?
* Which features influence the predictions?
* Is the model biased toward specific customer groups?
* Does it satisfy the business success criteria?

In this phase, participants will perform a comprehensive evaluation of the optimized model and generate explainability and bias reports using **Amazon SageMaker Clarify**.

---

# Learning Objectives

By the end of this phase, participants will be able to:

* Evaluate machine learning models using multiple performance metrics.
* Understand why Accuracy is not sufficient for imbalanced datasets.
* Interpret confusion matrices, ROC curves, and Precision–Recall curves.
* Generate SHAP-based feature importance.
* Explain individual predictions.
* Detect bias using SageMaker Clarify.
* Decide whether a model is ready for production.

---

# Enterprise Architecture

```text
                    Optimized Model
                           │
                           ▼
                  Test Dataset (15%)
                           │
                           ▼
                  Model Evaluation
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    Performance      Explainability        Bias
      Metrics          (SHAP)           Detection
          │                │                │
          └────────────────┼────────────────┘
                           ▼
              Evaluation & Clarify Reports
                           │
                           ▼
               Production Readiness Decision
```

---

# Why Evaluate the Model?

A model with **95% Accuracy** may still perform poorly if the dataset is imbalanced.

Example:

| Actual   | Predicted | Result |
| -------- | --------- | ------ |
| No Churn | No Churn  | ✅      |
| No Churn | No Churn  | ✅      |
| No Churn | No Churn  | ✅      |
| Churn    | No Churn  | ❌      |

Accuracy:

```text
75%
```

However,

The model detected **0 customers likely to churn**, making it ineffective for the business.

---

# Input

From Phase 5:

```text
Best Model

Test Dataset

Hyperparameter Configuration
```

---

# Expected Output

```text
Evaluation Report

Confusion Matrix

ROC Curve

Precision-Recall Curve

Feature Importance

SHAP Analysis

Bias Report

Clarify Report
```

---

# Task 1 – Load the Test Dataset

```python
test = pd.read_csv("test.csv")

test.head()
```

Split the dataset.

```python
X_test = test.drop("churn", axis=1)

y_test = test["churn"]
```

---

Expected Result

Testing dataset ready.

---

# Task 2 – Load the Best Model

Load the model artifact generated in Phase 5.

Example

```python
import joblib

model = joblib.load("best_model.joblib")
```

If using a SageMaker endpoint, invoke the endpoint instead of loading locally.

---

# Task 3 – Generate Predictions

```python
predictions = model.predict(X_test)

probabilities = model.predict_proba(X_test)[:,1]
```

---

Expected Result

Two outputs

* Binary prediction
* Churn probability

---

# Task 4 – Calculate Evaluation Metrics

Import

```python
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)
```

Compute

```python
accuracy = accuracy_score(y_test,predictions)

precision = precision_score(y_test,predictions)

recall = recall_score(y_test,predictions)

f1 = f1_score(y_test,predictions)

auc = roc_auc_score(y_test,probabilities)
```

Display

```python
print("Accuracy:",accuracy)

print("Precision:",precision)

print("Recall:",recall)

print("F1:",f1)

print("ROC AUC:",auc)
```

---

### Discussion

Which metric is most important?

For churn prediction:

* Recall is critical because missing a customer who is about to churn has a direct business cost.
* ROC AUC measures how well the model separates churners from non-churners across thresholds.

---

# Task 5 – Generate a Confusion Matrix

```python
from sklearn.metrics import confusion_matrix

cm = confusion_matrix(y_test,predictions)

print(cm)
```

Example

|            | Predicted No | Predicted Yes |
| ---------- | ------------ | ------------- |
| Actual No  | 220          | 15            |
| Actual Yes | 18           | 47            |

---

### Discussion

Explain:

* True Positive
* False Positive
* True Negative
* False Negative

Business impact:

False Negatives are the most expensive because potential churners are not targeted for retention.

---

# Task 6 – Generate Classification Report

```python
from sklearn.metrics import classification_report

print(classification_report(
    y_test,
    predictions
))
```

Expected Output

```text
Precision

Recall

F1

Support
```

---

# Task 7 – Generate ROC Curve

```python
from sklearn.metrics import RocCurveDisplay

RocCurveDisplay.from_predictions(
    y_test,
    probabilities
)
```

Discussion

* What does the ROC curve represent?
* Why is a larger AUC desirable?

---

# Task 8 – Generate Precision–Recall Curve

```python
from sklearn.metrics import PrecisionRecallDisplay

PrecisionRecallDisplay.from_predictions(
    y_test,
    probabilities
)
```

Discussion

Why use a Precision–Recall curve?

* It provides better insight for imbalanced datasets.

---

# Task 9 – Feature Importance

If using XGBoost:

```python
importance = model.feature_importances_
```

Create a ranking.

Example

| Rank | Feature             |
| ---- | ------------------- |
| 1    | Satisfaction Score  |
| 2    | Support Calls       |
| 3    | Outstanding Balance |
| 4    | Contract Type       |
| 5    | Monthly Charges     |

Discussion

* Do these align with business expectations?
* Which features are actionable?

---

# Task 10 – Explain Predictions with SageMaker Clarify

## Objective

Generate SHAP explanations.

Clarify computes the contribution of each feature to a prediction.

Workflow

```text
Model

↓

Clarify Processing Job

↓

SHAP Values

↓

Feature Contribution Report
```

Expected Output

* Global feature importance
* Local explanations
* SHAP values

Discussion

How can explainability improve stakeholder trust?

---

# Task 11 – Interpret SHAP Results

Example

Customer A

| Feature                 | Contribution |
| ----------------------- | ------------ |
| Low Satisfaction        | +0.29        |
| High Support Calls      | +0.21        |
| Month-to-Month Contract | +0.15        |
| Long Tenure             | -0.11        |

Discussion

Explain:

Positive values increase churn probability.

Negative values decrease churn probability.

---

# Task 12 – Bias Detection with SageMaker Clarify

## Objective

Evaluate whether predictions differ unfairly across protected groups.

Example protected attributes:

* Gender
* Region
* Age Group

Clarify produces metrics such as:

* Class Imbalance
* Difference in Positive Prediction Rates
* Demographic Parity
* Conditional Demographic Disparity

Discussion

Could the model unfairly disadvantage a customer segment?

---

# Task 13 – Analyze Business KPIs

Compare evaluation metrics against the original business goals.

| KPI       | Target | Actual | Status |
| --------- | ------ | ------ | ------ |
| ROC AUC   | >0.90  | 0.94   | ✅      |
| Precision | >85%   | 88%    | ✅      |
| Recall    | >80%   | 86%    | ✅      |
| F1 Score  | >85%   | 87%    | ✅      |

Discussion

Does the model satisfy business expectations?

---

# Task 14 – Generate Evaluation Report

Prepare a report containing:

* Dataset summary
* Model configuration
* Hyperparameters
* Accuracy
* Precision
* Recall
* F1 Score
* ROC AUC
* Confusion Matrix
* ROC Curve
* Precision–Recall Curve
* Feature Importance
* SHAP Analysis
* Bias Analysis
* Production readiness recommendation

---

# Best Practices

* Always evaluate on the untouched test dataset.
* Report multiple metrics, not Accuracy alone.
* Use Precision–Recall curves for imbalanced datasets.
* Validate that feature importance aligns with business logic.
* Perform bias assessment before production deployment.
* Keep evaluation reports under version control for auditability.

---

# Deliverables

Participants should submit:

1. Evaluation notebook.
2. Confusion Matrix.
3. ROC Curve.
4. Precision–Recall Curve.
5. Classification Report.
6. Feature Importance chart.
7. SHAP explainability report.
8. SageMaker Clarify bias report.
9. Final production readiness assessment.

---

# Validation Checklist

| Validation                           | Expected Result |
| ------------------------------------ | --------------- |
| Test dataset used                    | ✓               |
| Predictions generated                | ✓               |
| Evaluation metrics calculated        | ✓               |
| Confusion Matrix created             | ✓               |
| ROC Curve generated                  | ✓               |
| Precision–Recall Curve generated     | ✓               |
| Feature Importance available         | ✓               |
| SHAP report generated                | ✓               |
| Bias analysis completed              | ✓               |
| Production recommendation documented | ✓               |

---

# Discussion Questions

1. Why is Accuracy alone an insufficient metric for churn prediction?
2. What business risks arise from a high number of False Negatives?
3. How do ROC and Precision–Recall curves complement each other?
4. Why are SHAP values preferred over simple feature importance for explainability?
5. How can bias affect customer trust and regulatory compliance?
6. Should a highly accurate model be deployed if it exhibits significant bias?

---

# Transition to Phase 7

By the end of this phase, participants have a thoroughly evaluated and explainable model. The next step is to ensure the **training process itself is robust and reproducible**.

In **Phase 7 – Model Debugging, Model Registry, and Production Deployment Preparation**, participants will:

* Use **Amazon SageMaker Debugger** to inspect training behavior and identify issues such as overfitting or unstable gradients.
* Register the approved model in **SageMaker Model Registry** with versioning and metadata.
* Prepare the model for controlled promotion into production as part of an enterprise MLOps workflow.
