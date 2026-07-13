# Aula 1 — Slide 49 — RECURSIVE FEATURE ELIMINATION (RFE)

from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(max_iter=10000)
rfe = RFE(model, n_features_to_select=10, step=1)
rfe.fit(X_train_sc, y_train)

# Features selecionadas
selected = X.columns[rfe.support_]
print('Features selecionadas:', selected.tolist())
print('Ranking:', rfe.ranking_)

# Avaliar
acc = rfe.score(X_test_sc, y_test)
print(f'Acurácia com RFE: {acc:.4f}')
