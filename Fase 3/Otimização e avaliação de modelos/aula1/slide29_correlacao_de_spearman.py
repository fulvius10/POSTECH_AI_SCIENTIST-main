# Aula 1 — Slide 29 — CORRELAÇÃO DE SPEARMAN

# Spearman: usa rankings em vez de valores brutos
from scipy.stats import spearmanr

# Calcular para cada feature
for col in X.columns:
    corr, pval = spearmanr(X[col], y)
    if abs(corr) > 0.5:
        print(f'{col}: r={corr:.3f}, p={pval:.2e}')
