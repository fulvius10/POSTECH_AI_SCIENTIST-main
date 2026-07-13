# Aula 5 — Slide 18 — DIAGNÓSTICO AUTOMÁTICO COM LEARNING CURVE

# Diagnóstico automático
gap = val_mean[-1] - train_mean[-1]
abs_err = val_mean[-1]

if abs_err > 1.0 and gap < 0.2:
    diagnosis = 'UNDERFITTING'
    action = 'Aumente a complexidade do modelo'
elif gap > 0.5:
    diagnosis = 'OVERFITTING'
    action = 'Regularize ou adicione mais dados'
else:
    diagnosis = 'BOM AJUSTE'
    action = 'Modelo generaliza bem!'

print(f'Diagnóstico: {diagnosis}')
print(f'Ação: {action}')
print(f'Erro de validação: {abs_err:.4f}')
print(f'Gap treino-validação: {gap:.4f}')
