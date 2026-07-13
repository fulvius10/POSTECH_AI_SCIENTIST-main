# Aula 3 — Slide 56 — DETECTANDO INTERAÇÕES

# Forçar uma feature de interação específica
shap.dependence_plot(
    'worst radius',           # feature principal
    shap_values, X_test,
    interaction_index='worst concave points',  # interação forçada
    show=False
)
plt.savefig('interaction_plot.png', bbox_inches='tight', dpi=150)
plt.close()

# Interpretar: se a cor muda o padrão vertical,
# há interação entre as duas features.
# Ex: 'worst radius' tem efeito positivo SOMENTE quando
# 'worst concave points' é alto (pontos vermelhos no topo)
