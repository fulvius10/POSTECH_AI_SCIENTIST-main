# Aula 3 — Slide 36 — FORCE PLOT INTERATIVO

# Force Plot interativo (HTML) para múltiplas instâncias
# Ideal para dashboards e notebooks

# Inicializar visualização JS
shap.initjs()

# Force plot interativo (abre no notebook)
shap.force_plot(
    expected_value,
    shap_values[:50],      # primeiras 50 instâncias
    X_test.iloc[:50]
)

# Salvar como HTML
force_html = shap.force_plot(
    expected_value,
    shap_values[:50],
    X_test.iloc[:50]
)
shap.save_html('force_plot_interativo.html', force_html)
