# Aula 3 — Slide 37 — IMPORTÂNCIA MÉDIA ABSOLUTA

# Importância global: média dos valores absolutos dos SHAP values
importancia = pd.DataFrame({
    'feature': X_test.columns,
    'importance': np.abs(shap_values).mean(0)
}).sort_values('importance', ascending=False)

print('=== Top 15 Features (SHAP) ===')
for i, row in importancia.head(15).iterrows():
    bar = '█' * int(row['importance'] * 50)
    print(f"{row['feature']:25s}  {row['importance']:.4f}  {bar}")

# Bar plot nativo do SHAP
shap.summary_plot(shap_values, X_test, plot_type='bar', show=False)
plt.savefig('bar_plot_shap.png', bbox_inches='tight', dpi=150)
plt.close()
