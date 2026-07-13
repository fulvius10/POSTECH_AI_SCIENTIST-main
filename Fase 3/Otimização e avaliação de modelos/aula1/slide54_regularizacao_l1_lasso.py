# Aula 1 — Slide 54 — REGULARIZAÇÃO L1 (LASSO)

from sklearn.linear_model import Lasso, LogisticRegression
from sklearn.feature_selection import SelectFromModel

# Logistic Regression com L1 (para classificação)
lr_l1 = LogisticRegression(
    penalty='l1', solver='liblinear', 
    C=0.1, max_iter=10000
)
lr_l1.fit(X_train_sc, y_train)

# Features com coeficiente != 0
sel_l1 = SelectFromModel(lr_l1, prefit=True)
X_tr_l1 = sel_l1.transform(X_train_sc)
X_te_l1 = sel_l1.transform(X_test_sc)

print(f'Features mantidas: {X_tr_l1.shape[1]} de {X_train_sc.shape[1]}')
print(f'Features zeradas: {(lr_l1.coef_[0] == 0).sum()}')
