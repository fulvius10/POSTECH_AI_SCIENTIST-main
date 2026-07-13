# Aula 4 — Slide 18 — AVALIAÇÃO FINAL NO TESTE

# Após escolher o melhor modelo na VALIDAÇÃO:
best_model = GradientBoostingClassifier(
    n_estimators=100, random_state=42
)

# Retreinar com treino + validação
import numpy as np
X_full_train = np.vstack([X_train, X_val])
y_full_train = np.hstack([y_train, y_val])
best_model.fit(X_full_train, y_full_train)

# Avaliação FINAL no teste (UMA VEZ!)
y_test_pred = best_model.predict(X_test)
y_test_proba = best_model.predict_proba(X_test)[:, 1]

print('=== AVALIAÇÃO FINAL (TESTE) ===')
print(classification_report(y_test, y_test_pred))
print(f'AUC-ROC: {roc_auc_score(y_test, y_test_proba):.4f}')
