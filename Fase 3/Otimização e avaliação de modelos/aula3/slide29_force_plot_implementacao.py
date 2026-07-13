# Aula 3 — Slide 29 — FORCE PLOT: IMPLEMENTAÇÃO

# Explicação de uma única previsão (instância 0)
instance = X_test.iloc[0]

# Force Plot com matplotlib (para salvar como imagem)
shap.force_plot(
    expected_value,           # valor base
    shap_values[0],           # SHAP values desta instância
    instance,                 # valores das features
    matplotlib=True,
    show=False
)
plt.savefig('force_plot.png', bbox_inches='tight', dpi=150)
plt.close()

# Verificar a previsão
pred = model.predict_proba(instance.values.reshape(1,-1))[0]
print(f'Previsão: classe {pred.argmax()} ({pred.max():.4f})')
print(f'Valor base: {expected_value:.4f}')
print(f'Soma SHAP: {shap_values[0].sum():.4f}')
