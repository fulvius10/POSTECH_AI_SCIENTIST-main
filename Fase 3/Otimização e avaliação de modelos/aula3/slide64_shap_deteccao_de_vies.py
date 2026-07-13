# Aula 3 — Slide 64 — SHAP: DETECÇÃO DE VIÉS

# Exemplo: verificar se o modelo é justo entre grupos
# Supondo uma coluna 'gender' no dataset

# Comparar SHAP values médios entre grupos
group_a = shap_values[X_test['worst texture'] > X_test['worst texture'].median()]
group_b = shap_values[X_test['worst texture'] <= X_test['worst texture'].median()]

print('=== Comparação de grupos ===')
for i, feat in enumerate(X_test.columns[:5]):
    diff = np.abs(group_a[:, i].mean() - group_b[:, i].mean())
    if diff > 0.1:
        print(f'⚠️ {feat}: diferença de {diff:.4f} entre grupos')
    else:
        print(f'✅ {feat}: diferença de {diff:.4f} (ok)')
