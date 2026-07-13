# Aula 2 — Slide 52 — OPTUNA: IMPLEMENTAÇÃO BÁSICA

import optuna
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score

def objective(trial):
    # Espaço de busca definido DENTRO da função
    C = trial.suggest_float('C', 0.01, 1000, log=True)
    kernel = trial.suggest_categorical('kernel', ['rbf', 'poly', 'sigmoid'])
    gamma = trial.suggest_float('gamma', 0.0001, 10, log=True)

    model = SVC(C=C, kernel=kernel, gamma=gamma)
    score = cross_val_score(model, X_train, y_train, cv=5,
                            scoring='accuracy').mean()
    return score

# Criar study e otimizar
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100, timeout=600)

print(f'Melhor score: {study.best_value:.4f}')
print(f'Melhores HPs: {study.best_params}')
