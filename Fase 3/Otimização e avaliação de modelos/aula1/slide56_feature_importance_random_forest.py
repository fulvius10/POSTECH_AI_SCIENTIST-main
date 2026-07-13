# Aula 1 — Slide 56 — FEATURE IMPORTANCE: RANDOM FOREST

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train_sc, y_train)

# Feature importances
importances = pd.Series(rf.feature_importances_, index=X.columns)
importances = importances.sort_values(ascending=False)
print('Top 10 features:')
print(importances.head(10))

# Selecionar via limiar
sel_rf = SelectFromModel(rf, prefit=True, threshold='mean')
X_tr_rf = sel_rf.transform(X_train_sc)
print(f'\nFeatures acima da média: {X_tr_rf.shape[1]}')
