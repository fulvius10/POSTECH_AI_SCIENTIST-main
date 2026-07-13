# Aula 5 — Slide 39 — ENCONTRANDO O ALPHA IDEAL

from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import Ridge, Lasso

# Buscar melhor alpha via CV
alphas = np.logspace(-4, 4, 50)  # 0.0001 a 10000

for name, Model in [('Ridge', Ridge), ('Lasso', Lasso)]:
    grid = GridSearchCV(
        Model(max_iter=10000),
        {'alpha': alphas},
        cv=5,
        scoring='neg_mean_squared_error',
        n_jobs=-1
    )
    grid.fit(X_train, y_train)
    print(f'{name:6s} | Melhor α: {grid.best_params_["alpha"]:.6f} | '
          f'CV MSE: {-grid.best_score_:.4f} | '
          f'Teste MSE: {mean_squared_error(y_test, grid.predict(X_test)):.4f}')
