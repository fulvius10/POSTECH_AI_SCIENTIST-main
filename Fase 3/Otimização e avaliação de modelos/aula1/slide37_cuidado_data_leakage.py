# Aula 1 — Slide 37 — CUIDADO: DATA LEAKAGE

# CORRETO: fit_transform apenas no TREINO, transform no TESTE
sel.fit_transform(X_train, y_train)
sel.transform(X_test)

# ERRADO: dar fit em todos os dados vaza informação do teste (leakage)
# sel.fit_transform(X_ALL, y_ALL)   # Leakage!
# Nunca usar fit no conjunto de teste!
