# Aula 3 — Slide 52 — BAR PLOT: VERSÃO EXECUTIVA

# Bar Plot: importância média absoluta (mais simples)
shap.summary_plot(
    shap_values, X_test,
    plot_type='bar',  # ← tipo bar
    max_display=15,
    show=False
)
plt.savefig('bar_plot.png', bbox_inches='tight', dpi=150)
plt.close()

# Também pode criar manualmente para mais controle
importancia = pd.DataFrame({
    'feature': X_test.columns,
    'importance': np.abs(shap_values).mean(0)
}).sort_values('importance', ascending=True).tail(15)

plt.figure(figsize=(8, 6))
plt.barh(importancia['feature'], importancia['importance'])
plt.xlabel('Mean |SHAP value|')
plt.title('Feature Importance (SHAP)')
plt.tight_layout()
plt.savefig('custom_bar.png', dpi=150)
