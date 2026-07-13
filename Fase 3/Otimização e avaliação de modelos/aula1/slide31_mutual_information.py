# Aula 1 — Slide 31 — MUTUAL INFORMATION

from sklearn.feature_selection import mutual_info_classif

# Mutual Information para classificação
mi_scores = mutual_info_classif(X_train, y_train, random_state=42)

# Ranquear features por MI
mi_ranking = pd.Series(mi_scores, index=X.columns)
mi_ranking = mi_ranking.sort_values(ascending=False)
print(mi_ranking.head(10))
