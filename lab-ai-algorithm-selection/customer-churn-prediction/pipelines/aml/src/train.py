"""Optuna-tuned LightGBM or CatBoost (objective: validation PR-AUC).

Runs on the low-priority ``cpu-tuning-spot`` cluster. Writes the best model to
``--model-dir`` (``model.bst`` for LightGBM, ``model.cbm`` for CatBoost) plus
``params.json`` / ``metrics.json``, and logs the study to MLflow.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import lightgbm as lgb
import mlflow
import optuna
from catboost import CatBoostClassifier
from common import LABEL_COL, feature_columns, read_split, write_json
from sklearn.metrics import average_precision_score


def lgb_objective(trial, x_tr, y_tr, x_va, y_va):
    params = {
        "objective": "binary",
        "verbosity": -1,
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 15, 255, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 20, 500, log=True),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.5, 1.0),
        "bagging_freq": 1,
        "lambda_l2": trial.suggest_float("lambda_l2", 1e-3, 10.0, log=True),
        "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1.0, 20.0, log=True),
    }
    booster = lgb.train(
        params,
        lgb.Dataset(x_tr, y_tr),
        num_boost_round=2000,
        valid_sets=[lgb.Dataset(x_va, y_va)],
        callbacks=[lgb.early_stopping(100, verbose=False)],
    )
    score = average_precision_score(y_va, booster.predict(x_va))
    trial.set_user_attr("model", booster)
    return score


def cat_objective(trial, x_tr, y_tr, x_va, y_va):
    model = CatBoostClassifier(
        iterations=2000,
        learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        depth=trial.suggest_int("depth", 4, 10),
        l2_leaf_reg=trial.suggest_float("l2_leaf_reg", 1.0, 20.0, log=True),
        scale_pos_weight=trial.suggest_float("scale_pos_weight", 1.0, 20.0, log=True),
        eval_metric="PRAUC",
        early_stopping_rounds=100,
        verbose=False,
        thread_count=-1,
    )
    model.fit(x_tr, y_tr, eval_set=(x_va, y_va))
    score = average_precision_score(y_va, model.predict_proba(x_va)[:, 1])
    trial.set_user_attr("model", model)
    return score


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--algorithm", choices=["lightgbm", "catboost"], required=True)
    p.add_argument("--train-data", required=True)
    p.add_argument("--valid-data", required=True)
    p.add_argument("--n-trials", type=int, default=60)
    p.add_argument("--model-dir", required=True)
    args = p.parse_args()

    train, valid = read_split(args.train_data), read_split(args.valid_data)
    features = feature_columns(train)
    x_tr, y_tr = train[features], train[LABEL_COL].astype(int)
    x_va, y_va = valid[features], valid[LABEL_COL].astype(int)

    objective = lgb_objective if args.algorithm == "lightgbm" else cat_objective
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=7))
    study.optimize(lambda t: objective(t, x_tr, y_tr, x_va, y_va), n_trials=args.n_trials)
    best = study.best_trial

    out = Path(args.model_dir)
    out.mkdir(parents=True, exist_ok=True)
    model = best.user_attrs["model"]
    if args.algorithm == "lightgbm":
        model.save_model(str(out / "model.bst"))
    else:
        model.save_model(str(out / "model.cbm"))
    write_json(
        {"algorithm": args.algorithm, "features": features, **best.params}, out / "params.json"
    )
    write_json({"valid_pr_auc": best.value, "n_trials": len(study.trials)}, out / "metrics.json")
    mlflow.log_params({f"{args.algorithm}_{k}": v for k, v in best.params.items()})
    mlflow.log_metric(f"{args.algorithm}_valid_pr_auc", best.value)


if __name__ == "__main__":
    main()
