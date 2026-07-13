# Aula 2 — Slide 37 — COARSE → FINE SEARCH

# ETAPA 1: Busca ampla (coarse search)
param_coarse = {
    'C': [0.01, 0.1, 1, 10, 100, 1000],
    'gamma': [0.0001, 0.001, 0.01, 0.1, 1]
}
grid_coarse = GridSearchCV(SVC(), param_coarse, cv=5)
grid_coarse.fit(X_train, y_train)
print(f'Melhor região: C={grid_coarse.best_params_["C"]}, '
      f'gamma={grid_coarse.best_params_["gamma"]}')

# ETAPA 2: Refinamento (fine search) ao redor do melhor
# Se coarse encontrou C=10, gamma=0.01:
param_fine = {
    'C': [5, 7, 10, 15, 20],            # zoom em C=10
    'gamma': [0.005, 0.008, 0.01, 0.015, 0.02]  # zoom em gamma=0.01
}
grid_fine = GridSearchCV(SVC(), param_fine, cv=5)
grid_fine.fit(X_train, y_train)
print(f'Refinado: {grid_fine.best_params_}')
print(f'Score: {grid_fine.best_score_:.4f}')
