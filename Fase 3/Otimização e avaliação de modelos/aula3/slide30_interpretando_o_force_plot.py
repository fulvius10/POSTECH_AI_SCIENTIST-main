# Aula 3 — Slide 30 — INTERPRETANDO O FORCE PLOT

# Top features que mais contribuíram (positiva e negativamente)
contribs = pd.DataFrame({
    'feature': X_test.columns,
    'shap_value': shap_values[0],
    'feature_value': instance.values
}).sort_values('shap_value', key=abs, ascending=False)

print('=== Top 10 contribuições ===')
for _, row in contribs.head(10).iterrows():
    direction = '↑' if row['shap_value'] > 0 else '↓'
    print(f"{direction} {row['feature']:25s} = {row['feature_value']:.4f}"
          f"  →  SHAP = {row['shap_value']:+.4f}")
