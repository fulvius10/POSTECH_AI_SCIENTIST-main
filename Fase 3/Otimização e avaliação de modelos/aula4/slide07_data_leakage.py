# Aula 4 — Slide 7 — DATA LEAKAGE:

# ✅ CORRETO: divisão em 3 conjuntos
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.25, stratify=y_temp, random_state=42)
# 0.25 de 80% = 20% do total → 60% treino, 20% val, 20% teste
