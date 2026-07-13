# Aula 4 — Slide 33 — WALK-FORWARD COM TIMESERIESSPLIT

from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

tscv = TimeSeriesSplit(n_splits=5)
rmse_scores, mae_scores = [], []

for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X[train_idx], y[train_idx])
    preds = model.predict(X[val_idx])

    rmse = np.sqrt(mean_squared_error(y[val_idx], preds))
    mae = mean_absolute_error(y[val_idx], preds)
    rmse_scores.append(rmse)
    mae_scores.append(mae)
    print(f'Fold {fold}: RMSE={rmse:.2f} | MAE={mae:.2f}')

print(f'\nRMSE Médio: {np.mean(rmse_scores):.2f} ± {np.std(rmse_scores):.2f}')
print(f'MAE Médio:  {np.mean(mae_scores):.2f} ± {np.std(mae_scores):.2f}')
