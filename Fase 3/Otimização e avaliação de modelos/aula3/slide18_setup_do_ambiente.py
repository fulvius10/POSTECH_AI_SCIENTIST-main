# Aula 3 — Slide 18 — SETUP DO AMBIENTE

import shap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_breast_cancer
import xgboost as xgb

# Dataset: diagnóstico de câncer de mama (569 amostras, 30 features)
data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = data.target
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Treinar modelo XGBoost
model = xgb.XGBClassifier(
    n_estimators=100, max_depth=5,
    learning_rate=0.1, random_state=42
)
model.fit(X_train, y_train)
print(f'Acurácia no teste: {model.score(X_test, y_test):.4f}')
