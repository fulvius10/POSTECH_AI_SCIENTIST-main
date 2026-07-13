# Aula 1 — Slide 32 — VARIANCE THRESHOLD

from sklearn.feature_selection import VarianceThreshold

# Remover features com variância < 0.1
selector = VarianceThreshold(threshold=0.1)
X_high_var = selector.fit_transform(X_train_sc)

print(f'Features originais: {X_train_sc.shape[1]}')
print(f'Features após filtro: {X_high_var.shape[1]}')
print('Features removidas:', 
      X.columns[~selector.get_support()].tolist())
