# Aula 5 — Slide 31 — LASSO (L1): IMPLEMENTAÇÃO

from sklearn.linear_model import Lasso

for alpha in [0.001, 0.01, 0.1, 1, 10]:
    model = Pipeline([
        ('poly', PolynomialFeatures(10)),
        ('scaler', StandardScaler()),
        ('lasso', Lasso(alpha=alpha, max_iter=10000))
    ])
    model.fit(X_train, y_train)
    tr = mean_squared_error(y_train, model.predict(X_train))
    te = mean_squared_error(y_test, model.predict(X_test))

    coefs = model.named_steps['lasso'].coef_
    n_zero = (coefs == 0).sum()
    sparsity = n_zero / len(coefs) * 100

    print(f'α={alpha:6.3f} | Treino={tr:.4f} | Teste={te:.4f} | '
          f'Zerados: {n_zero}/{len(coefs)} ({sparsity:.0f}%)')
