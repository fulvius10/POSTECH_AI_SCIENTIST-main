"""Aplica o modelo treinado a novos pedidos e gera uma fila de priorizacao.

Exemplo:
    python src/score_new_orders.py --input data/raw/desafio_nps_fase_1.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = PROJECT_DIR / "models" / "detractor_classifier.joblib"
DEFAULT_OUTPUT = PROJECT_DIR / "data" / "processed" / "scored_orders.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="CSV com novos pedidos.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def risk_band(probability: pd.Series) -> pd.Categorical:
    """Traduz probabilidade em uma fila operacional simples."""
    return pd.cut(
        probability,
        bins=[-0.01, 0.50, 0.75, 1.00],
        labels=["Baixo", "Alto", "Critico"],
    )


def main() -> None:
    args = parse_args()
    model = joblib.load(args.model)
    data = pd.read_csv(args.input)
    required_features = list(model.feature_names_in_)
    missing = sorted(set(required_features).difference(data.columns))
    if missing:
        raise ValueError(f"Colunas necessarias ausentes: {missing}")

    result = data.copy()
    result["detractor_probability"] = model.predict_proba(data[required_features])[:, 1]
    result["risk_band"] = risk_band(result["detractor_probability"])
    result = result.sort_values("detractor_probability", ascending=False)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"{len(result)} pedidos pontuados. Saida: {args.output}")


if __name__ == "__main__":
    main()

