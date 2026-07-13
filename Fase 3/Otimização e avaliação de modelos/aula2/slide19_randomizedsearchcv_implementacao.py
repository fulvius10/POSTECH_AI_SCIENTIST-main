# Aula 2 — Slide 19 — RANDOMIZEDSEARCHCV: IMPLEMENTAÇÃO

from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import uniform, randint, loguniform

# Definir DISTRIBUIÇÕES (não listas fixas)
param_dist = {
    'C': loguniform(0.01, 1000),         # escala log!
    'kernel': ['rbf', 'poly', 'sigmoid'],
    'gamma': loguniform(0.0001, 10),
}

# RandomizedSearchCV: 50 combinações aleatórias
random_search = RandomizedSearchCV(
    SVC(), param_dist, n_iter=50, cv=5,
    scoring='accuracy', n_jobs=-1,
    random_state=42, verbose=1
)
random_search.fit(X_train, y_train)

print(f'Melhor score: {random_search.best_score_:.4f}')
print(f'Melhores HPs: {random_search.best_params_}')
