# Aula 2 — Slide 31 — TIME SERIES SPLIT

from sklearn.model_selection import TimeSeriesSplit

# TimeSeriesSplit: validação sempre POSTERIOR ao treino
tscv = TimeSeriesSplit(n_splits=5)

for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
    print(f'Fold {fold}: treino[:{train_idx[-1]}] → val[{val_idx[0]}:{val_idx[-1]}]')

# Usar no GridSearchCV para dados temporais
grid_ts = GridSearchCV(SVC(), param_grid, cv=tscv, scoring='accuracy')
grid_ts.fit(X_train, y_train)
