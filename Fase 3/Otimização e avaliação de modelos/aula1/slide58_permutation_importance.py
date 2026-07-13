# Aula 1 — Slide 58 — PERMUTATION IMPORTANCE

from sklearn.inspection import permutation_importance

result = permutation_importance(
    rf, X_test_sc, y_test,
    n_repeats=10, random_state=42
)

perm_imp = pd.Series(
    result.importances_mean, index=X.columns
).sort_values(ascending=False)
print('Top 10 (Permutation Importance):')
print(perm_imp.head(10))
