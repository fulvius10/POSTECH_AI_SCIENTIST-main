# Aula 4 — Slide 36 — MAPE: ERRO PERCENTUAL

# MAPE: Mean Absolute Percentage Error
def mape(y_true, y_pred):
    mask = y_true != 0  # evitar divisão por zero
    return np.mean(np.abs(
        (y_true[mask] - y_pred[mask]) / y_true[mask]
    )) * 100

# Calcular MAPE para cada fold
for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X[train_idx], y[train_idx])
    preds = model.predict(X[val_idx])

    fold_mape = mape(y[val_idx], preds)
    rmse = np.sqrt(mean_squared_error(y[val_idx], preds))
    print(f'Fold {fold}: RMSE={rmse:.2f} | MAPE={fold_mape:.2f}%')
