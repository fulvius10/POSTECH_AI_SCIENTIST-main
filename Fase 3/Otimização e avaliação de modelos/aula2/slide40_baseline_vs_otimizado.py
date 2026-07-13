# Aula 2 — Slide 40 — BASELINE VS. OTIMIZADO

from sklearn.metrics import accuracy_score, classification_report

# 1. Baseline: hiperparâmetros padrão
baseline = RandomForestClassifier(random_state=42)
baseline.fit(X_train, y_train)
acc_base = accuracy_score(y_test, baseline.predict(X_test))

# 2. Otimizado via GridSearchCV
acc_opt = grid_rf.score(X_test, y_test)

print(f'Baseline  (default HPs): {acc_base:.4f}')
print(f'Otimizado (GridSearchCV): {acc_opt:.4f}')
print(f'Ganho: +{(acc_opt - acc_base)*100:.2f}%')

# Report detalhado do melhor modelo
print('\n', classification_report(
    y_test, grid_rf.predict(X_test)
))
