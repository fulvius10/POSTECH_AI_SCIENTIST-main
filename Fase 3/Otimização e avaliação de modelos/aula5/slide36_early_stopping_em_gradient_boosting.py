# Aula 5 — Slide 36 — EARLY STOPPING EM GRADIENT BOOSTING

from sklearn.ensemble import GradientBoostingClassifier

# GBM com early stopping via warm_start
gbm = GradientBoostingClassifier(
    n_estimators=1000,  # máximo
    max_depth=5,
    learning_rate=0.1,
    validation_fraction=0.2,  # 20% para validação interna
    n_iter_no_change=10,      # early stopping: 10 rounds
    random_state=42
)
gbm.fit(X_train, y_train)
print(f'Árvores usadas: {gbm.n_estimators_} de 1000')
print(f'Acurácia teste: {gbm.score(X_test, y_test):.4f}')

# XGBoost com early stopping
import xgboost as xgb
xgb_model = xgb.XGBClassifier(n_estimators=1000, learning_rate=0.1,
    early_stopping_rounds=10, eval_metric='logloss')
xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
print(f'XGB árvores: {xgb_model.best_iteration}')
