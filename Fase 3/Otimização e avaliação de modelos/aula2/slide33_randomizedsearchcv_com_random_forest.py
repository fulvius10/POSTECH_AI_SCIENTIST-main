# Aula 2 — Slide 33 — RANDOMIZEDSEARCHCV COM RANDOM FOREST

from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint, uniform

param_dist_rf = {
    'n_estimators': randint(50, 500),
    'max_depth': [5, 10, 20, 30, None],
    'min_samples_split': randint(2, 20),
    'min_samples_leaf': randint(1, 10),
    'max_features': ['sqrt', 'log2', None]
}

random_rf = RandomizedSearchCV(
    RandomForestClassifier(random_state=42),
    param_dist_rf, n_iter=100, cv=skf,
    scoring='accuracy', n_jobs=-1,
    random_state=42, verbose=1
)
random_rf.fit(X_train, y_train)
print(f'Melhor score CV: {random_rf.best_score_:.4f}')
print(f'Melhores HPs: {random_rf.best_params_}')
