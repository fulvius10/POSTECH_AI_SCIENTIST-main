# Aula 2 — Slide 62 — MODELO FINAL: PIPELINE COMPLETO

# Pipeline completo: Optuna → treino final → avaliação

# 1. Otimizar com Optuna
study = optuna.create_study(direction='maximize')
study.optimize(objective_rf, n_trials=200)

# 2. Treinar modelo final com os MELHORES HPs
best_params = study.best_params
final_model = RandomForestClassifier(**best_params, random_state=42)
final_model.fit(X_train, y_train)  # treino completo

# 3. Avaliar no teste (INTOCADO até agora)
from sklearn.metrics import classification_report
y_pred = final_model.predict(X_test)
print(classification_report(y_test, y_pred))

# 4. Documentar
print(f'Melhores HPs: {best_params}')
print(f'Trials realizados: {len(study.trials)}')
print(f'Melhor CV score: {study.best_value:.4f}')
print(f'Score no teste: {final_model.score(X_test, y_test):.4f}')
