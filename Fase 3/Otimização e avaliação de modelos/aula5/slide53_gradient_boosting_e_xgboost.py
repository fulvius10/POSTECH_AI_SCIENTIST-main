# Aula 5 — Slide 53 — GRADIENT BOOSTING E XGBOOST

from sklearn.ensemble import GradientBoostingClassifier
import xgboost as xgb

# Gradient Boosting (sklearn)
gbm = GradientBoostingClassifier(
    n_estimators=200, max_depth=5,
    learning_rate=0.1, random_state=42
)
gbm.fit(X_train, y_train)
print(f'GBM Acurácia: {gbm.score(X_test, y_test):.4f}')

# XGBoost (mais rápido, mais features)
xgb_model = xgb.XGBClassifier(
    n_estimators=200, max_depth=5,
    learning_rate=0.1, random_state=42,
    eval_metric='logloss'
)
xgb_model.fit(X_train, y_train)
print(f'XGB Acurácia: {xgb_model.score(X_test, y_test):.4f}')
