# Aula 4 — Slide 37 — COMPARANDO MODELOS EM SÉRIES TEMPORAIS

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
import xgboost as xgb

models = {
    'LinearReg': LinearRegression(),
    'RF': RandomForestRegressor(n_estimators=100, random_state=42),
    'GBM': GradientBoostingRegressor(n_estimators=100, random_state=42),
}

for name, model in models.items():
    rmse_list = []
    for train_idx, val_idx in tscv.split(X):
        model.fit(X[train_idx], y[train_idx])
        preds = model.predict(X[val_idx])
        rmse_list.append(np.sqrt(mean_squared_error(y[val_idx], preds)))
    print(f'{name:12s} | RMSE: {np.mean(rmse_list):.2f} ± '
          f'{np.std(rmse_list):.2f}')
