# Aula 3 — Slide 20 — VERIFICANDO A EFICIÊNCIA

# Propriedade de Eficiência: soma dos SHAP values deve ser
# igual à previsão do modelo menos o valor base

for i in range(5):
    prediction = model.predict_proba(X_test.iloc[[i]])[0][1]
    shap_sum = shap_values[i].sum() + expected_value
    print(f'Instância {i}:')
    print(f'  Previsão do modelo:   {prediction:.6f}')
    print(f'  Valor base + Σ SHAP: {shap_sum:.6f}')
    print(f'  Diferença:           {abs(prediction - shap_sum):.10f}')
    print()

# Resultado: diferença = ~0 (ponto flutuante)
# → Explicação COMPLETA, sem resíduo!
