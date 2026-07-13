# Aula 2 — Slide 58 — BENCHMARK:

import time

results = {}

# 1. Grid Search
t0 = time.time()
grid_search.fit(X_train, y_train)
results['Grid'] = {
    'score': grid_search.best_score_,
    'time': time.time() - t0,
    'evals': len(grid_search.cv_results_['params'])
}

# 2. Random Search
t0 = time.time()
random_search.fit(X_train, y_train)
results['Random'] = {
    'score': random_search.best_score_,
    'time': time.time() - t0,
    'evals': 50
}

# 3. Bayesian (Optuna)
t0 = time.time()
study.optimize(objective, n_trials=50)
results['Bayesian'] = {
    'score': study.best_value,
    'time': time.time() - t0,
    'evals': 50
}

for name, r in results.items():
    print(f'{name:10s} | Score: {r["score"]:.4f} | '
          f'Tempo: {r["time"]:.1f}s | Evals: {r["evals"]}')
