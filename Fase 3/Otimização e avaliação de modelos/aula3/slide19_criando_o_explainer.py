# Aula 3 — Slide 19 — CRIANDO O EXPLAINER

# TreeExplainer para XGBoost (rápido e exato)
explainer = shap.TreeExplainer(model)

# Calcular SHAP values para todo o conjunto de teste
shap_values = explainer.shap_values(X_test)

# Para classificação binária com RF, shap_values é uma lista
# Usamos [1] para a classe positiva
if isinstance(shap_values, list):
    shap_values = shap_values[1]

expected_value = explainer.expected_value
if isinstance(expected_value, list):
    expected_value = expected_value[1]

print(f'Shape dos SHAP values: {shap_values.shape}')
print(f'Valor base (expected value): {expected_value:.4f}')
print(f'Cada linha = 1 instância, cada coluna = 1 feature')
