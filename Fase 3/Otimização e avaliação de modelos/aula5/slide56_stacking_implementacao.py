# Aula 5 — Slide 56 — STACKING: IMPLEMENTAÇÃO

from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC

# Base models (diversos!)
estimators = [
    ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
    ('gbm', GradientBoostingClassifier(n_estimators=100, random_state=42)),
    ('svm', SVC(probability=True, random_state=42))
]

# Meta-modelo: Logistic Regression aprende a combinar
stacking = StackingClassifier(
    estimators=estimators,
    final_estimator=LogisticRegression(),
    cv=5  # usa 5-fold CV para gerar features do meta-modelo
)

stacking.fit(X_train, y_train)
print(f'Stacking Acurácia: {stacking.score(X_test, y_test):.4f}')
