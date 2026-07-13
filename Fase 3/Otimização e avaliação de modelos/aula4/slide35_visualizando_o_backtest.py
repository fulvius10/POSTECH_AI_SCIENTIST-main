# Aula 4 — Slide 35 — VISUALIZANDO O BACKTEST

# Plotar previsões vs reais do último fold
model = RandomForestRegressor(n_estimators=100, random_state=42)
last_train, last_val = list(tscv.split(X))[-1]
model.fit(X[last_train], y[last_train])
preds = model.predict(X[last_val])

dates_val = df['date'].iloc[last_val]

plt.figure(figsize=(12, 5))
plt.plot(dates_val, y[last_val], label='Real', color='white', alpha=0.8)
plt.plot(dates_val, preds, label='Previsto', color='#D30F59', linewidth=2)
plt.fill_between(dates_val,
    preds - np.std(y[last_val] - preds),
    preds + np.std(y[last_val] - preds),
    alpha=0.2, color='#D30F59')
plt.legend()
plt.title('Backtest: Previsão vs Real')
plt.ylabel('Vendas')
plt.savefig('backtest_plot.png', dpi=150, bbox_inches='tight')
