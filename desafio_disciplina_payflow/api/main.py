"""API REST para inferencia do score PayFlow."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "payflow_default_model.joblib"
MODEL_BUNDLE: dict = {}


class CreditApplication(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "idade": 35,
                "renda_mensal": 5200.0,
                "tempo_emprego_anos": 6.0,
                "autonomo": 0,
                "score_credito": 680.0,
                "valor_solicitado": 8000.0,
                "prazo_meses": 24,
                "juros_mensal_pct": 2.1,
                "qtde_cartoes": 2,
                "qtde_contratos_abertos": 1,
                "utilizacao_credito": 0.35,
                "inadimplencias_anteriores": 0,
                "dias_atraso_max_12m": 5,
                "reclamacoes_6m": 0,
                "possui_avalista": 0,
                "canal_aquisicao": "app",
                "regiao": "Sudeste",
                "tipo_produto": "emprestimo_pessoal",
            }
        },
    )

    idade: int = Field(ge=18, le=100, description="Usada somente para auditoria; nao entra no modelo.")
    renda_mensal: float | None = Field(default=None, ge=0)
    tempo_emprego_anos: float | None = Field(default=None, ge=0, le=80)
    autonomo: Literal[0, 1]
    score_credito: float = Field(ge=300, le=900)
    valor_solicitado: float = Field(gt=0)
    prazo_meses: int = Field(gt=0, le=120)
    juros_mensal_pct: float = Field(ge=0, le=30)
    qtde_cartoes: int = Field(ge=0, le=100)
    qtde_contratos_abertos: int = Field(ge=0, le=100)
    utilizacao_credito: float = Field(ge=0, le=1)
    inadimplencias_anteriores: int = Field(ge=0)
    dias_atraso_max_12m: int = Field(ge=0, le=365)
    reclamacoes_6m: int = Field(ge=0)
    possui_avalista: Literal[0, 1]
    canal_aquisicao: Literal["app", "site", "loja", "parceiro"]
    regiao: Literal["Sudeste", "Sul", "Nordeste", "Norte", "Centro-Oeste"]
    tipo_produto: Literal["emprestimo_pessoal", "cartao", "bnpl"]


class PredictionResponse(BaseModel):
    default_probability: float
    threshold: float
    predicted_default: int
    risk_band: str
    recommended_action: str
    model_version: str
    target_version: str


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not MODEL_PATH.exists():
        raise RuntimeError("Modelo nao encontrado. Execute src/train_model.py primeiro.")
    MODEL_BUNDLE.update(joblib.load(MODEL_PATH))
    yield
    MODEL_BUNDLE.clear()


app = FastAPI(
    title="PayFlow Credit Risk API",
    version="1.0.0",
    description="Probabilidade de default nos primeiros 90 dias apos a concessao.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "model_version": MODEL_BUNDLE.get("model_version", "not_loaded"),
        "target_version": MODEL_BUNDLE.get("target_version", "not_loaded"),
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(application: CreditApplication) -> PredictionResponse:
    if not MODEL_BUNDLE:
        raise HTTPException(status_code=503, detail="Modelo indisponivel")

    payload = application.model_dump()
    frame = pd.DataFrame([{column: payload.get(column) for column in MODEL_BUNDLE["feature_columns"]}])
    probability = float(MODEL_BUNDLE["pipeline"].predict_proba(frame)[0, 1])
    threshold = float(MODEL_BUNDLE["threshold"])

    if probability < threshold / 2:
        risk_band = "baixo"
    elif probability < threshold:
        risk_band = "moderado"
    elif probability < 0.50:
        risk_band = "alto"
    else:
        risk_band = "critico"

    predicted_default = int(probability >= threshold)
    action = "seguir_politica_de_credito" if predicted_default == 0 else "revisao_manual_obrigatoria"
    return PredictionResponse(
        default_probability=round(probability, 6),
        threshold=threshold,
        predicted_default=predicted_default,
        risk_band=risk_band,
        recommended_action=action,
        model_version=MODEL_BUNDLE["model_version"],
        target_version=MODEL_BUNDLE["target_version"],
    )
