# Aula 2 — Slide 54 — OPTUNA: VISUALIZAÇÕES

import optuna.visualization as viz

# 1. Histórico de otimização
fig1 = viz.plot_optimization_history(study_rf)
fig1.show()

# 2. Importância dos hiperparâmetros
fig2 = viz.plot_param_importances(study_rf)
fig2.show()

# 3. Relação entre HPs (contour plot)
fig3 = viz.plot_contour(study_rf, params=['n_estimators','max_depth'])
fig3.show()

# 4. Coordenadas paralelas
fig4 = viz.plot_parallel_coordinate(study_rf)
fig4.show()

# 5. Slice plot por parâmetro
fig5 = viz.plot_slice(study_rf)
fig5.show()
