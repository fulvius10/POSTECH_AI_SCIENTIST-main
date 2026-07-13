# Aula 2 — Slide 38 — ANALISANDO RESULTADOS DO GRIDSEARCHCV

import pandas as pd

# Resultados detalhados do GridSearchCV
results = pd.DataFrame(grid_rf.cv_results_)
results = results.sort_values('rank_test_score')

# Top 5 combinações
print(results[[
    'params', 'mean_test_score', 'std_test_score',
    'mean_train_score', 'rank_test_score'
]].head())

# Detectar overfitting: gap treino vs validação
results['gap'] = results['mean_train_score'] - results['mean_test_score']
print(f'\nGap médio treino-validação: {results["gap"].mean():.4f}')
if results['gap'].mean() > 0.05:
    print('⚠️ Possível overfitting - considere regularizar!')
