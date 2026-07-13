# Aula 3 — Slide 35 — DECISION PLOT

# Decision Plot: visualizar contribuições de múltiplas instâncias
# Traça uma linha por instância, acumulando contribuições

# Todas as instâncias do teste
shap.decision_plot(
    expected_value, shap_values,
    X_test, show=False
)
plt.savefig('decision_plot.png', bbox_inches='tight', dpi=150)
plt.close()

# Comparar corretos vs incorretos
correct = preds == y_test
shap.decision_plot(
    expected_value, shap_values[~correct],
    X_test[~correct],
    title='Previsões INCORRETAS',
    show=False
)
plt.savefig('decision_incorrect.png', bbox_inches='tight', dpi=150)
plt.close()
