# Aula 3 — Slide 39 — KERNELEXPLAINER

from sklearn.neural_network import MLPClassifier

# Modelo: rede neural
mlp = MLPClassifier(hidden_layer_sizes=(100, 50),
                    max_iter=500, random_state=42)
mlp.fit(X_train, y_train)
print(f'MLP Acurácia: {mlp.score(X_test, y_test):.4f}')

# KernelExplainer: funciona com QUALQUER modelo
# Usa amostra dos dados de treino como background
background = shap.sample(X_train, 100)  # amostra para velocidade
explainer_kernel = shap.KernelExplainer(
    mlp.predict_proba, background
)

# Calcular SHAP values (mais lento que TreeExplainer!)
shap_values_mlp = explainer_kernel.shap_values(
    X_test.iloc[:20]  # apenas 20 instâncias (lento!)
)
