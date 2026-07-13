# Aula 1 — Slide 57 — FEATURE IMPORTANCE: XGBOOST

import xgboost as xgb

xgb_clf = xgb.XGBClassifier(
    n_estimators=100, max_depth=5,
    learning_rate=0.1, random_state=42,
    eval_metric='logloss'
)
xgb_clf.fit(X_train_sc, y_train)

# Feature importances (gain, weight, cover)
imp = pd.Series(
    xgb_clf.feature_importances_, index=X.columns
).sort_values(ascending=False)
print('Top 10 features (XGBoost):')
print(imp.head(10))

# Selecionar
sel_xgb = SelectFromModel(xgb_clf, prefit=True)
X_tr_xgb = sel_xgb.transform(X_train_sc)
print(f'Features selecionadas: {X_tr_xgb.shape[1]}')
