# Aula 4 — Slide 17 — MÉTRICAS DE REGRESSÃO: IMPLEMENTAÇÃO

from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score
)
import numpy as np

# Supondo y_test e y_pred já calculados
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

# MAPE manual (cuidado com zeros!)
mask = y_test != 0
mape = np.mean(np.abs((y_test[mask] - y_pred[mask]) / y_test[mask])) * 100

print(f'MAE:  {mae:.4f}')
print(f'RMSE: {rmse:.4f}')
print(f'R²:   {r2:.4f}')
print(f'MAPE: {mape:.2f}%')

# Visualizar previsão vs real
plt.figure(figsize=(8, 6))
plt.scatter(y_test, y_pred, alpha=0.5, color='#D30F59')
plt.plot([y_test.min(), y_test.max()],
         [y_test.min(), y_test.max()], 'k--', alpha=0.5)
plt.xlabel('Real'); plt.ylabel('Previsto')
plt.title(f'Real vs Previsto (R²={r2:.4f})')
plt.savefig('scatter_pred.png', dpi=150)
