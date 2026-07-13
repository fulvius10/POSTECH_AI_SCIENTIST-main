# Aula 5 — Slide 17 — EXPERIMENTO: COMPLEXIDADE CRESCENTE

from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error

degrees = [1, 2, 3, 5, 10, 20]
for deg in degrees:
    model = Pipeline([
        ('poly', PolynomialFeatures(deg)),
        ('lin', LinearRegression())
    ])
    model.fit(X_train, y_train)
    tr_err = mean_squared_error(y_train, model.predict(X_train))
    te_err = mean_squared_error(y_test, model.predict(X_test))

    status = ('UNDERFITTING' if tr_err > 0.5 and te_err > 0.5
              else 'OVERFITTING' if te_err > tr_err * 2
              else 'BOM AJUSTE')
    print(f'Grau {deg:2d} | Treino={tr_err:.3f} | '
          f'Teste={te_err:.3f} | {status}')
