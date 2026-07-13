# Aula 1 — Slide 50 — RFECV: RFE COM VALIDAÇÃO CRUZADA

from sklearn.feature_selection import RFECV

rfecv = RFECV(
    estimator=LogisticRegression(max_iter=10000),
    step=1,
    cv=5,  # 5-fold cross-validation
    scoring='accuracy',
    min_features_to_select=1
)
rfecv.fit(X_train_sc, y_train)

print(f'Número ótimo de features: {rfecv.n_features_}')
print(f'Features selecionadas: {X.columns[rfecv.support_].tolist()}')
print(f'Acurácia: {rfecv.score(X_test_sc, y_test):.4f}')
