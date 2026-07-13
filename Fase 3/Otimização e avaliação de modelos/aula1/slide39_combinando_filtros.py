# Aula 1 — Slide 39 — COMBINANDO FILTROS

from sklearn.pipeline import Pipeline

# Pipeline: VarianceThreshold → SelectKBest
pipe = Pipeline([
    ('variance', VarianceThreshold(threshold=0.1)),
    ('kbest', SelectKBest(f_classif, k=10)),
    ('clf', LogisticRegression(max_iter=10000))
])

pipe.fit(X_train_sc, y_train)
acc = pipe.score(X_test_sc, y_test)
print(f'Pipeline Filter → Acurácia: {acc:.4f}')
