# Aula 2 — Slide 55 — OPTUNA: XGBOOST COM EARLY STOPPING

import xgboost as xgb

def objective_xgb(trial):
    params = {
        'learning_rate': trial.suggest_float('lr', 0.001, 0.3, log=True),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample', 0.5, 1.0),
        'n_estimators': trial.suggest_int('n_estimators', 50, 500),
        'reg_alpha': trial.suggest_float('alpha', 1e-8, 10, log=True),
        'reg_lambda': trial.suggest_float('lambda', 1e-8, 10, log=True),
    }
    model = xgb.XGBClassifier(**params, eval_metric='logloss',
                               random_state=42)
    score = cross_val_score(model, X_train, y_train,
                            cv=5, scoring='accuracy').mean()
    return score

study_xgb = optuna.create_study(direction='maximize')
study_xgb.optimize(objective_xgb, n_trials=150)
print(f'XGBoost melhor: {study_xgb.best_value:.4f}')
