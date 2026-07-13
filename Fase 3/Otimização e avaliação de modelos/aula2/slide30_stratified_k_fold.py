# Aula 2 — Slide 30 — STRATIFIED K-FOLD

from sklearn.model_selection import StratifiedKFold

# Stratified K-Fold com 5 folds
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Usar no GridSearchCV
grid = GridSearchCV(
    SVC(), param_grid, cv=skf,  # ← Passa o StratifiedKFold aqui
    scoring='accuracy', n_jobs=-1
)
grid.fit(X_train, y_train)

# Ou usar diretamente com cross_val_score
scores = cross_val_score(SVC(C=1), X_train, y_train, cv=skf)
print(f'Scores: {scores}')
print(f'Média: {scores.mean():.4f} ± {scores.std():.4f}')
