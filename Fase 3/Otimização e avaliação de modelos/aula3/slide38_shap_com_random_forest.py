# Aula 3 — Slide 38 — SHAP COM RANDOM FOREST

from sklearn.ensemble import RandomForestClassifier

# Treinar Random Forest
rf = RandomForestClassifier(n_estimators=200, max_depth=10,
                            random_state=42)
rf.fit(X_train, y_train)
print(f'RF Acurácia: {rf.score(X_test, y_test):.4f}')

# TreeExplainer funciona com RF também!
explainer_rf = shap.TreeExplainer(rf)
shap_values_rf = explainer_rf.shap_values(X_test)

# Para RF binário, shap_values é lista [classe_0, classe_1]
shap_values_rf = shap_values_rf[1]  # classe positiva

# Waterfall da primeira instância
exp_rf = shap.Explanation(
    values=shap_values_rf[0],
    base_values=explainer_rf.expected_value[1],
    data=X_test.iloc[0].values,
    feature_names=X_test.columns.tolist()
)
shap.waterfall_plot(exp_rf, show=False)
plt.savefig('waterfall_rf.png', bbox_inches='tight', dpi=150)
