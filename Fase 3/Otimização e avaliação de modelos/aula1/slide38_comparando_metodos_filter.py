# Aula 1 — Slide 38 — COMPARANDO MÉTODOS FILTER

from sklearn.feature_selection import (
    SelectKBest, f_classif, chi2, mutual_info_classif
)
from sklearn.preprocessing import MinMaxScaler

results = {}
for name, scorer in [('ANOVA', f_classif),
                      ('MI', mutual_info_classif)]:
    sel = SelectKBest(scorer, k=10)
    Xtr = sel.fit_transform(X_train_sc, y_train)
    Xte = sel.transform(X_test_sc)
    clf = LogisticRegression(max_iter=10000)
    clf.fit(Xtr, y_train)
    acc = accuracy_score(y_test, clf.predict(Xte))
    results[name] = acc
    print(f'{name:8s} → Acurácia: {acc:.4f}')
