# Aula 2 — Slide 18 — GRIDSEARCHCV: IMPLEMENTAÇÃO

from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

# Definir a grade de hiperparâmetros
param_grid = {
    'C': [0.1, 1, 10, 100],
    'kernel': ['rbf', 'poly'],
    'gamma': ['scale', 'auto', 0.01, 0.1]
}

# GridSearchCV com 5-fold CV
grid_search = GridSearchCV(
    SVC(), param_grid, cv=5,
    scoring='accuracy', n_jobs=-1, verbose=1
)
grid_search.fit(X_train, y_train)

print(f'Melhor score: {grid_search.best_score_:.4f}')
print(f'Melhores HPs: {grid_search.best_params_}')
print(f'Combinações testadas: {len(grid_search.cv_results_["params"])}')
