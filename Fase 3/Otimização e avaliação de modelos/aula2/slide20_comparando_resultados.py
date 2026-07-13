# Aula 2 — Slide 20 — COMPARANDO RESULTADOS

from sklearn.metrics import classification_report

# Modelo final com os melhores hiperparâmetros
print('=== Grid Search ===')
print(f'Melhor CV score: {grid_search.best_score_:.4f}')
print(f'Score no teste:  {grid_search.score(X_test, y_test):.4f}')

print('\n=== Random Search ===')
print(f'Melhor CV score: {random_search.best_score_:.4f}')
print(f'Score no teste:  {random_search.score(X_test, y_test):.4f}')

# Classification report do melhor modelo
y_pred = random_search.predict(X_test)
print('\n', classification_report(y_test, y_pred))
