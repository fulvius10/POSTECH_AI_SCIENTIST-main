# Aula 3 — Slide 50 — SUMMARY PLOT: O QUE É?

# Summary Plot (beeswarm) — visão global completa
plt.figure(figsize=(10, 8))
shap.summary_plot(shap_values, X_test, show=False)
plt.savefig('summary_plot.png', bbox_inches='tight', dpi=150)
plt.close()
