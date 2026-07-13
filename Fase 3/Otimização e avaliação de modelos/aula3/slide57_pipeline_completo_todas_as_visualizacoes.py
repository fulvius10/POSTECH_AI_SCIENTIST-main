# Aula 3 — Slide 57 — PIPELINE COMPLETO: TODAS AS VISUALIZAÇÕES

# === PIPELINE COMPLETO DE ANÁLISE SHAP ===

# 1. Treinar modelo
model.fit(X_train, y_train)

# 2. Criar explainer
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# 3. Visão global
shap.summary_plot(shap_values, X_test)           # Beeswarm
shap.summary_plot(shap_values, X_test, plot_type='bar')  # Bar

# 4. Dependence (top features)
for feat in top_features[:3]:
    shap.dependence_plot(feat, shap_values, X_test)

# 5. Explicação local
for idx in [0, 10, 50]:  # instâncias representativas
    exp = shap.Explanation(values=shap_values[idx],
        base_values=explainer.expected_value,
        data=X_test.iloc[idx].values,
        feature_names=X_test.columns.tolist())
    shap.waterfall_plot(exp)

# 6. Decision plot
shap.decision_plot(explainer.expected_value, shap_values, X_test)
