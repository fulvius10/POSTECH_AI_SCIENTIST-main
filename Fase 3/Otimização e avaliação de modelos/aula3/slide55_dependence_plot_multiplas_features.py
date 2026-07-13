# Aula 3 — Slide 55 — DEPENDENCE PLOT: MÚLTIPLAS FEATURES

# Dependence plot para as top 6 features
top_features = pd.Series(
    np.abs(shap_values).mean(0), index=X_test.columns
).sort_values(ascending=False).head(6).index

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
for ax, feat in zip(axes.flatten(), top_features):
    shap.dependence_plot(
        feat, shap_values, X_test,
        ax=ax, show=False
    )
    ax.set_title(feat, fontsize=12)

plt.tight_layout()
plt.savefig('dependence_grid.png', dpi=150)
plt.close()
