# Aula 3 — Slide 34 — COMPARANDO INSTÂNCIAS

# Comparar 2 instâncias com previsões opostas
from sklearn.metrics import accuracy_score

preds = model.predict(X_test)

# Encontrar uma previsão positiva e uma negativa
pos_idx = np.where(preds == 1)[0][0]
neg_idx = np.where(preds == 0)[0][0]

for idx, label in [(pos_idx, 'Positivo'), (neg_idx, 'Negativo')]:
    exp = shap.Explanation(
        values=shap_values[idx],
        base_values=expected_value,
        data=X_test.iloc[idx].values,
        feature_names=X_test.columns.tolist()
    )
    shap.waterfall_plot(exp, max_display=10, show=False)
    plt.title(f'Previsão: {label}')
    plt.savefig(f'waterfall_{label.lower()}.png',
                bbox_inches='tight', dpi=150)
    plt.close()
