"""Treina e avalia o score de inadimplencia PayFlow.

O script implementa as etapas de entendimento dos dados, preparacao,
modelagem e avaliacao do CRISP-DM. As informacoes futuras sao removidas antes
da divisao treino/teste para impedir leakage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_predict,
    cross_validate,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "payflow_credit_risk.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

TARGET = "default_90d"
ID_COLUMN = "id_cliente"
LEAKAGE_COLUMNS = [
    "parcelas_pagas_ate_3m",
    "atraso_primeira_parcela_dias",
    "status_apos_90d",
]
# Idade permanece na analise de equidade, mas nao participa da decisao automatizada.
GOVERNANCE_EXCLUDED_COLUMNS = ["idade"]
CATEGORICAL_FEATURES = ["canal_aquisicao", "regiao", "tipo_produto"]

RANDOM_STATE = 42
TEST_SIZE = 0.25
FALSE_NEGATIVE_COST = 10_000.0
FALSE_POSITIVE_COST = 500.0


def ensure_directories() -> None:
    for directory in (PROCESSED_DIR, MODELS_DIR, REPORTS_DIR, FIGURES_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ]
    )


def model_pipeline(model: Any, numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(numeric_features, categorical_features)),
            ("model", model),
        ]
    )


def probability_metrics(y_true: pd.Series, probabilities: np.ndarray, threshold: float = 0.5) -> dict[str, float | int]:
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    return {
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "average_precision": float(average_precision_score(y_true, probabilities)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def threshold_table(y_true: pd.Series, probabilities: np.ndarray) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    for threshold in np.round(np.arange(0.02, 0.81, 0.01), 2):
        metrics = probability_metrics(y_true, probabilities, float(threshold))
        cost = metrics["fn"] * FALSE_NEGATIVE_COST + metrics["fp"] * FALSE_POSITIVE_COST
        rows.append({"threshold": float(threshold), **metrics, "estimated_cost_brl": float(cost)})
    return pd.DataFrame(rows)


def outlier_summary(df: pd.DataFrame, numeric_columns: list[str]) -> pd.DataFrame:
    rows = []
    for column in numeric_columns:
        series = df[column].dropna()
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((series < lower) | (series > upper)).sum())
        rows.append(
            {
                "column": column,
                "q1": float(q1),
                "q3": float(q3),
                "lower_bound": float(lower),
                "upper_bound": float(upper),
                "outlier_count_iqr": count,
                "outlier_pct": float(count / len(series) * 100),
            }
        )
    return pd.DataFrame(rows).sort_values("outlier_pct", ascending=False)


def segment_metrics(scored: pd.DataFrame, group_column: str) -> pd.DataFrame:
    rows = []
    for group, part in scored.groupby(group_column, observed=False):
        if part[TARGET].nunique() < 2:
            auc = np.nan
        else:
            auc = roc_auc_score(part[TARGET], part["default_probability"])
        rows.append(
            {
                group_column: str(group),
                "records": int(len(part)),
                "default_rate": float(part[TARGET].mean()),
                "roc_auc": None if np.isnan(auc) else float(auc),
                "mean_predicted_probability": float(part["default_probability"].mean()),
            }
        )
    return pd.DataFrame(rows)


def plot_outputs(
    df: pd.DataFrame,
    y_test: pd.Series,
    model_probabilities: dict[str, np.ndarray],
    chosen_name: str,
    chosen_probabilities: np.ndarray,
    chosen_threshold: float,
    importance_df: pd.DataFrame,
    thresholds_df: pd.DataFrame,
) -> None:
    sns.set_theme(style="whitegrid", context="notebook")

    counts = df[TARGET].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=["Sem default", "Default em 90 dias"], y=counts.values, hue=["Sem default", "Default em 90 dias"], legend=False, palette=["#2E74B5", "#C23B3B"], ax=ax)
    for index, value in enumerate(counts.values):
        ax.text(index, value + 45, f"{value:,}\n({value / len(df):.1%})", ha="center", fontweight="bold")
    ax.set(title="Distribuicao do target", xlabel="", ylabel="Clientes")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "01_target_distribution.png", dpi=180)
    plt.close(fig)

    missing = df.isna().sum().sort_values(ascending=False)
    missing = missing[missing > 0]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.barplot(x=missing.values, y=missing.index, color="#D99A2B", ax=ax)
    for i, value in enumerate(missing.values):
        ax.text(value + 8, i, f"{value} ({value / len(df):.1%})", va="center")
    ax.set(title="Valores ausentes que exigem tratamento", xlabel="Quantidade", ylabel="")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "02_missing_values.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for name, probabilities in model_probabilities.items():
        fpr, tpr, _ = roc_curve(y_test, probabilities)
        axes[0].plot(fpr, tpr, label=f"{name} (AUC={roc_auc_score(y_test, probabilities):.3f})")
        precision, recall, _ = precision_recall_curve(y_test, probabilities)
        axes[1].plot(recall, precision, label=f"{name} (AP={average_precision_score(y_test, probabilities):.3f})")
    axes[0].plot([0, 1], [0, 1], "--", color="gray")
    axes[0].set(title="Curva ROC", xlabel="Taxa de falso positivo", ylabel="Taxa de verdadeiro positivo")
    axes[1].axhline(y_test.mean(), linestyle="--", color="gray", label=f"Prevalencia={y_test.mean():.3f}")
    axes[1].set(title="Curva Precisao-Recall", xlabel="Recall", ylabel="Precisao")
    axes[0].legend(fontsize=8)
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "03_model_curves.png", dpi=180)
    plt.close(fig)

    predictions = (chosen_probabilities >= chosen_threshold).astype(int)
    cm = confusion_matrix(y_test, predictions, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax)
    ax.set(title=f"Matriz de confusao - {chosen_name}\nthreshold={chosen_threshold:.2f}", xlabel="Predito", ylabel="Real", xticklabels=["Sem default", "Default"], yticklabels=["Sem default", "Default"])
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "04_confusion_matrix.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(thresholds_df["threshold"], thresholds_df["estimated_cost_brl"] / 1_000_000, color="#2E74B5", linewidth=2)
    best = thresholds_df.loc[thresholds_df["estimated_cost_brl"].idxmin()]
    ax.axvline(best["threshold"], color="#C23B3B", linestyle="--", label=f"Escolhido: {best['threshold']:.2f}")
    ax.set(title="Custo ilustrativo por threshold (validacao cruzada)", xlabel="Threshold", ylabel="Custo estimado (R$ milhoes)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "05_threshold_cost.png", dpi=180)
    plt.close(fig)

    top = importance_df.head(12).sort_values("importance_mean")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top["feature"], top["importance_mean"], xerr=top["importance_std"], color="#2E74B5", alpha=0.9)
    ax.axvline(0, color="#555555", linewidth=1)
    ax.set(title=f"Importancia por permutacao - {chosen_name}", xlabel="Queda media de Average Precision", ylabel="")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "06_feature_importance.png", dpi=180)
    plt.close(fig)

    observed, predicted = calibration_curve(y_test, chosen_probabilities, n_bins=8, strategy="quantile")
    fig, ax = plt.subplots(figsize=(6.8, 5.5))
    ax.plot([0, 1], [0, 1], "--", color="gray", label="Calibracao perfeita")
    ax.plot(predicted, observed, marker="o", linewidth=2, color="#2E74B5", label=chosen_name)
    ax.set(
        title="Curva de calibracao no holdout",
        xlabel="Probabilidade media prevista",
        ylabel="Frequencia observada de default",
        xlim=(0, max(0.5, float(predicted.max()) + 0.05)),
        ylim=(0, max(0.5, float(observed.max()) + 0.05)),
    )
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "07_calibration_curve.png", dpi=180)
    plt.close(fig)


def main() -> None:
    ensure_directories()
    df = pd.read_csv(DATA_PATH)

    original_numeric = df.select_dtypes(include=np.number).columns.tolist()
    quality = {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_ids": int(df[ID_COLUMN].duplicated().sum()),
        "default_count": int(df[TARGET].sum()),
        "default_rate": float(df[TARGET].mean()),
        "missing_by_column": {key: int(value) for key, value in df.isna().sum().items() if value > 0},
        "leakage_columns": LEAKAGE_COLUMNS,
        "governance_excluded_columns": GOVERNANCE_EXCLUDED_COLUMNS,
    }
    save_json(REPORTS_DIR / "data_quality.json", quality)
    outlier_summary(df, [column for column in original_numeric if column not in [ID_COLUMN, TARGET] + LEAKAGE_COLUMNS]).to_csv(REPORTS_DIR / "outlier_summary.csv", index=False)

    excluded = [ID_COLUMN, TARGET] + LEAKAGE_COLUMNS + GOVERNANCE_EXCLUDED_COLUMNS
    feature_columns = [column for column in df.columns if column not in excluded]
    categorical_features = [column for column in CATEGORICAL_FEATURES if column in feature_columns]
    numeric_features = [column for column in feature_columns if column not in categorical_features]

    X = df[feature_columns]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    candidates = {
        "Dummy (prevalencia)": DummyClassifier(strategy="prior"),
        "Regressao logistica": LogisticRegression(max_iter=2_000, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=350,
            min_samples_leaf=5,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    fitted: dict[str, Pipeline] = {}
    probabilities: dict[str, np.ndarray] = {}
    comparison_rows = []

    for name, estimator in candidates.items():
        pipeline = model_pipeline(estimator, numeric_features, categorical_features)
        cv_result = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring={"roc_auc": "roc_auc", "average_precision": "average_precision", "neg_brier": "neg_brier_score"},
            n_jobs=-1,
        )
        pipeline.fit(X_train, y_train)
        probability = pipeline.predict_proba(X_test)[:, 1]
        holdout = probability_metrics(y_test, probability)
        fitted[name] = pipeline
        probabilities[name] = probability
        comparison_rows.append(
            {
                "model": name,
                "cv_roc_auc_mean": float(cv_result["test_roc_auc"].mean()),
                "cv_roc_auc_std": float(cv_result["test_roc_auc"].std()),
                "cv_average_precision_mean": float(cv_result["test_average_precision"].mean()),
                "cv_average_precision_std": float(cv_result["test_average_precision"].std()),
                "cv_brier_mean": float(-cv_result["test_neg_brier"].mean()),
                **{f"holdout_{key}": value for key, value in holdout.items()},
            }
        )

    comparison_df = pd.DataFrame(comparison_rows).sort_values("cv_average_precision_mean", ascending=False)
    comparison_df.to_csv(REPORTS_DIR / "model_comparison.csv", index=False)
    selected_base_name = str(comparison_df.iloc[0]["model"])
    selected_base_pipeline = fitted[selected_base_name]
    # O objetivo e uma probabilidade. A calibracao sigmoid reduz a distancia
    # entre probabilidade prevista e frequencia observada sem usar o holdout.
    chosen_name = f"{selected_base_name} + calibracao sigmoid"
    chosen_pipeline = CalibratedClassifierCV(
        estimator=clone(selected_base_pipeline),
        method="sigmoid",
        cv=3,
    )
    chosen_pipeline.fit(X_train, y_train)
    chosen_probabilities = chosen_pipeline.predict_proba(X_test)[:, 1]
    probabilities[chosen_name] = chosen_probabilities

    oof_probabilities = cross_val_predict(
        clone(chosen_pipeline),
        X_train,
        y_train,
        cv=cv,
        method="predict_proba",
        n_jobs=-1,
    )[:, 1]
    thresholds_df = threshold_table(y_train, oof_probabilities)
    thresholds_df.to_csv(REPORTS_DIR / "threshold_analysis.csv", index=False)
    chosen_threshold = float(thresholds_df.loc[thresholds_df["estimated_cost_brl"].idxmin(), "threshold"])

    holdout_at_threshold = probability_metrics(y_test, chosen_probabilities, chosen_threshold)
    holdout_at_default = probability_metrics(y_test, chosen_probabilities, 0.5)

    permutation = permutation_importance(
        chosen_pipeline,
        X_test,
        y_test,
        scoring="average_precision",
        n_repeats=15,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    importance_df = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance_mean": permutation.importances_mean,
            "importance_std": permutation.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)
    importance_df.to_csv(REPORTS_DIR / "feature_importance.csv", index=False)

    scored_test = df.loc[X_test.index, [ID_COLUMN, "idade", "regiao", "tipo_produto", TARGET]].copy()
    scored_test["default_probability"] = chosen_probabilities
    scored_test["predicted_default"] = (chosen_probabilities >= chosen_threshold).astype(int)
    scored_test.to_csv(PROCESSED_DIR / "test_predictions.csv", index=False)
    segment_metrics(scored_test, "regiao").to_csv(REPORTS_DIR / "fairness_by_region.csv", index=False)
    scored_test["faixa_idade"] = pd.cut(scored_test["idade"], bins=[17, 29, 39, 49, 59, 120], labels=["18-29", "30-39", "40-49", "50-59", "60+"])
    segment_metrics(scored_test, "faixa_idade").to_csv(REPORTS_DIR / "fairness_by_age_band.csv", index=False)

    # Demonstra quantitativamente por que as colunas futuras nao podem entrar no modelo.
    leakage_features = feature_columns + LEAKAGE_COLUMNS
    leakage_categorical = categorical_features + ["status_apos_90d"]
    leakage_numeric = [column for column in leakage_features if column not in leakage_categorical]
    leakage_pipeline = model_pipeline(
        LogisticRegression(max_iter=2_000, random_state=RANDOM_STATE),
        leakage_numeric,
        leakage_categorical,
    )
    leakage_pipeline.fit(df.loc[X_train.index, leakage_features], y_train)
    leakage_probability = leakage_pipeline.predict_proba(df.loc[X_test.index, leakage_features])[:, 1]
    leakage_metrics = probability_metrics(y_test, leakage_probability)

    final_pipeline = clone(chosen_pipeline).fit(X, y)
    bundle = {
        "pipeline": final_pipeline,
        "model_name": chosen_name,
        "model_version": "1.0.0",
        "target_version": "default_90d_v1",
        "threshold": chosen_threshold,
        "feature_columns": feature_columns,
        "categorical_features": categorical_features,
        "numeric_features": numeric_features,
        "excluded_leakage_columns": LEAKAGE_COLUMNS,
        "governance_excluded_columns": GOVERNANCE_EXCLUDED_COLUMNS,
        "cost_assumptions_brl": {"false_negative": FALSE_NEGATIVE_COST, "false_positive": FALSE_POSITIVE_COST},
    }
    joblib.dump(bundle, MODELS_DIR / "payflow_default_model.joblib")

    metrics_payload = {
        "selected_model": chosen_name,
        "selected_base_model": selected_base_name,
        "selection_rule": "Maior Average Precision media na validacao cruzada estratificada; calibracao sigmoid aplicada sem usar o holdout.",
        "holdout_records": int(len(y_test)),
        "holdout_default_rate": float(y_test.mean()),
        "chosen_threshold": chosen_threshold,
        "metrics_at_0_50": holdout_at_default,
        "metrics_at_chosen_threshold": holdout_at_threshold,
        "leakage_demo_metrics": leakage_metrics,
        "cost_assumptions_brl": {"false_negative": FALSE_NEGATIVE_COST, "false_positive": FALSE_POSITIVE_COST},
    }
    save_json(REPORTS_DIR / "metrics.json", metrics_payload)
    plot_outputs(df, y_test, probabilities, chosen_name, chosen_probabilities, chosen_threshold, importance_df, thresholds_df)

    print(json.dumps(metrics_payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
