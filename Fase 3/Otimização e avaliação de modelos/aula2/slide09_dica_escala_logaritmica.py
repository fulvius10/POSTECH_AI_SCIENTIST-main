# Aula 2 — Slide 9 — DICA: ESCALA LOGARÍTMICA

# ❌ ERRADO: escala linear
param_grid = {'C': [0.001, 1, 2, 3, 4, 5, ..., 1000]}

# ✅ CORRETO: escala logarítmica
param_grid = {'C': [0.001, 0.01, 0.1, 1, 10, 100, 1000]}

# Ou via distribuição contínua (para Random Search)
from scipy.stats import loguniform
param_dist = {'C': loguniform(0.001, 1000)}
