# Aula 5 — Slide 32 — ELASTICNET: O MELHOR DOS DOIS

from sklearn.linear_model import ElasticNet

# l1_ratio controla a mistura: 0=Ridge, 1=Lasso, 0.5=meio-termo
for l1_ratio in [0.1, 0.3, 0.5, 0.7, 0.9]:
    model = Pipeline([
        ('poly', PolynomialFeatures(10)),
        ('scaler', StandardScaler()),
        ('enet', ElasticNet(alpha=0.1, l1_ratio=l1_ratio, max_iter=10000))
    ])
    model.fit(X_train, y_train)
    te = mean_squared_error(y_test, model.predict(X_test))
    coefs = model.named_steps['enet'].coef_
    n_zero = (coefs == 0).sum()
    print(f'l1_ratio={l1_ratio:.1f} | Teste={te:.4f} | '
          f'Zerados: {n_zero}/{len(coefs)}')
