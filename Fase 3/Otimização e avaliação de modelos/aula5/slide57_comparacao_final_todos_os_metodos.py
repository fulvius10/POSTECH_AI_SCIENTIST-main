# Aula 5 — Slide 57 — COMPARAÇÃO FINAL: TODOS OS MÉTODOS

from sklearn.metrics import accuracy_score, f1_score

models = {
    'Árvore Simples': DecisionTreeClassifier(max_depth=5, random_state=42),
    'Random Forest': RandomForestClassifier(200, random_state=42),
    'Gradient Boost': GradientBoostingClassifier(200, random_state=42),
    'XGBoost': xgb.XGBClassifier(200, learning_rate=0.1, random_state=42,
                                  eval_metric='logloss'),
    'Stacking': stacking,
}

print(f'{"Modelo":18s} | {"Acurácia":>8s} | {"F1":>6s}')
print('-' * 38)
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    print(f'{name:18s} | {acc:8.4f} | {f1:6.4f}')
