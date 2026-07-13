# Aula 1 — Slide 35 — EXEMPLO COMPLETO: PIPELINE FILTER

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

data = load_breast_cancer()
X, y = data.data, data.target
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42)

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc = scaler.transform(X_test)

sel = SelectKBest(f_classif, k=10)
X_tr_sel = sel.fit_transform(X_train_sc, y_train)
X_te_sel = sel.transform(X_test_sc)

clf = LogisticRegression(max_iter=10000)
clf.fit(X_tr_sel, y_train)
print(f'Acurácia: {accuracy_score(y_test, clf.predict(X_te_sel)):.4f}')
