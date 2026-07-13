# Aula 3 — Slide 54 — DEPENDENCE PLOT: O QUE É?

# Dependence Plot da feature mais importante
top_feature = pd.Series(
    np.abs(shap_values).mean(0), index=X_test.columns
).idxmax()

shap.dependence_plot(
    top_feature, shap_values, X_test,
    show=False
)
plt.savefig('dependence_plot.png', bbox_inches='tight', dpi=150)
plt.close()
