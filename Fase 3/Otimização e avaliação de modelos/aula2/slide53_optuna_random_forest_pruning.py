# Aula 2 — Slide 53 — OPTUNA: RANDOM FOREST + PRUNING

import optuna
from sklearn.ensemble import RandomForestClassifier

def objective_rf(trial):
    n_est = trial.suggest_int('n_estimators', 50, 500)
    max_d = trial.suggest_int('max_depth', 3, 30)
    min_ss = trial.suggest_int('min_samples_split', 2, 20)
    min_sl = trial.suggest_int('min_samples_leaf', 1, 10)
    max_f = trial.suggest_categorical('max_features', ['sqrt','log2',None])

    model = RandomForestClassifier(
        n_estimators=n_est, max_depth=max_d,
        min_samples_split=min_ss, min_samples_leaf=min_sl,
        max_features=max_f, random_state=42
    )
    score = cross_val_score(model, X_train, y_train,
                            cv=5, scoring='accuracy').mean()
    return score

study_rf = optuna.create_study(direction='maximize')
study_rf.optimize(objective_rf, n_trials=200, timeout=1200)
print(f'Melhor: {study_rf.best_value:.4f} | {study_rf.best_params}')
