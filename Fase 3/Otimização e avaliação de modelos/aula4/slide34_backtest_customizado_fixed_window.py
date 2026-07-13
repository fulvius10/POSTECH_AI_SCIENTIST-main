# Aula 4 — Slide 34 — BACKTEST CUSTOMIZADO: FIXED WINDOW

# Walk-Forward com FIXED WINDOW (janela fixa de 180 dias)
window_size = 180
step_size = 30  # avançar 30 dias por vez
results = []

for start in range(0, len(X) - window_size - step_size, step_size):
    train_end = start + window_size
    val_end = train_end + step_size

    X_tr, y_tr = X[start:train_end], y[start:train_end]
    X_vl, y_vl = X[train_end:val_end], y[train_end:val_end]

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_tr, y_tr)
    preds = model.predict(X_vl)

    rmse = np.sqrt(mean_squared_error(y_vl, preds))
    results.append({'start': start, 'end': val_end, 'rmse': rmse})

results_df = pd.DataFrame(results)
print(f'RMSE médio (Fixed Window): {results_df["rmse"].mean():.2f}')
print(f'RMSE std:                  {results_df["rmse"].std():.2f}')
