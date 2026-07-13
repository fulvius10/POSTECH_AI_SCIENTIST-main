# Aula 2 — Slide 39 — VISUALIZANDO IMPORTÂNCIA DOS HPS

import matplotlib.pyplot as plt
import numpy as np

# Performance vs. cada hiperparâmetro
results = pd.DataFrame(grid_rf.cv_results_)

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for ax, param in zip(axes, ['param_n_estimators',
                             'param_max_depth',
                             'param_min_samples_split']):
    grouped = results.groupby(param)['mean_test_score'].mean()
    ax.bar(range(len(grouped)), grouped.values)
    ax.set_xticklabels(grouped.index, rotation=45)
    ax.set_title(param.replace('param_', ''))
    ax.set_ylabel('Mean CV Score')

plt.tight_layout()
plt.savefig('hp_importance.png', dpi=150)
plt.show()
