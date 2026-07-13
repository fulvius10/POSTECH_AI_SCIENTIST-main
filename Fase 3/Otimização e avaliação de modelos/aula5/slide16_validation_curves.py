# Aula 5 — Slide 16 — VALIDATION CURVES

from sklearn.model_selection import validation_curve
from sklearn.ensemble import RandomForestRegressor

param_range = range(1, 21)
tr_s, val_s = validation_curve(
    RandomForestRegressor(n_estimators=50, random_state=42),
    X_train, y_train,
    param_name='max_depth', param_range=param_range,
    cv=5, scoring='neg_mean_squared_error', n_jobs=-1
)

train_mean = -tr_s.mean(axis=1)
val_mean = -val_s.mean(axis=1)
best_depth = list(param_range)[np.argmin(val_mean)]

plt.figure(figsize=(10, 6))
plt.plot(param_range, train_mean, label='Treino', color='#4CAF50')
plt.plot(param_range, val_mean, label='Validação', color='#D30F59')
plt.axvline(best_depth, color='#FFD54F', linestyle='--',
            label=f'Melhor max_depth={best_depth}')
plt.xlabel('max_depth')
plt.ylabel('Erro (MSE)')
plt.legend()
plt.title('Validation Curve')
print(f'Melhor max_depth: {best_depth}')
