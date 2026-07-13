# Aula 3 — Slide 33 — WATERFALL PLOT: IMPLEMENTAÇÃO

# Criar o objeto Explanation para a instância 0
explanation = shap.Explanation(
    values=shap_values[0],
    base_values=expected_value,
    data=instance.values,
    feature_names=X_test.columns.tolist()
)

# Waterfall Plot
shap.waterfall_plot(explanation, show=False)
plt.savefig('waterfall_plot.png', bbox_inches='tight', dpi=150)
plt.close()

# Para as top N features apenas:
shap.waterfall_plot(explanation, max_display=10, show=False)
plt.savefig('waterfall_top10.png', bbox_inches='tight', dpi=150)
plt.close()
