# Aula 2 — Slide 32 — IMPLEMENTAÇÃO: PIPELINE COMPLETO

from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier

# Modelo e grade
rf = RandomForestClassifier(random_state=42)
param_grid_rf = {
    'n_estimators': [100, 200, 500],
    'max_depth': [5, 10, 20, None],
    'min_samples_split': [2, 5, 10],
    'max_features': ['sqrt', 'log2']
}

# Stratified 5-Fold CV
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# GridSearchCV
grid_rf = GridSearchCV(
    rf, param_grid_rf, cv=skf,
    scoring='accuracy', n_jobs=-1, verbose=2,
    return_train_score=True  # para diagnóstico de overfitting
)
grid_rf.fit(X_train, y_train)
print(f'Total combinações: {len(grid_rf.cv_results_["params"])}')
print(f'Melhor score CV: {grid_rf.best_score_:.4f}')
print(f'Score teste: {grid_rf.score(X_test, y_test):.4f}')
