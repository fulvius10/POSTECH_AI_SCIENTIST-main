# Aula 5 — Slide 30 — RIDGE (L2): IMPLEMENTAÇÃO

from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import Pipeline
import numpy as np

# Modelo complexo (grau 10) COM Ridge
alphas = [0, 0.01, 0.1, 1, 10, 100]

for alpha in alphas:
    model = Pipeline([
        ('poly', PolynomialFeatures(10)),
        ('scaler', StandardScaler()),
        ('ridge', Ridge(alpha=alpha))
    ])
    model.fit(X_train, y_train)
    tr = mean_squared_error(y_train, model.predict(X_train))
    te = mean_squared_error(y_test, model.predict(X_test))
    n_coefs = len(model.named_steps['ridge'].coef_)
    print(f'α={alpha:6.2f} | Treino={tr:.4f} | Teste={te:.4f} | '
          f'Coefs: {n_coefs}')
