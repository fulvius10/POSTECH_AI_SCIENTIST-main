# Aula 5 — Slide 51 — RANDOM FOREST: O REI DO BAGGING

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

# Random Forest para classificação
rf = RandomForestClassifier(
    n_estimators=200,    # 200 árvores
    max_depth=10,        # profundidade máxima
    max_features='sqrt', # features por split = √n
    random_state=42,
    n_jobs=-1            # paralelizar!
)
rf.fit(X_train, y_train)
print(f'RF Acurácia: {rf.score(X_test, y_test):.4f}')

# Feature importance
importances = pd.Series(rf.feature_importances_, index=feature_names)
print('\nTop 5 features:')
print(importances.sort_values(ascending=False).head())
