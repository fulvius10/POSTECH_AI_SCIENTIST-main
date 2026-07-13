# Aula 1 — Slide 36 — VISUALIZANDO OS SCORES

import matplotlib.pyplot as plt
import numpy as np

# Scores do SelectKBest
scores = sel.scores_
feature_names = data.feature_names

# Top 15 features por score
top_idx = np.argsort(scores)[::-1][:15]

plt.figure(figsize=(10, 6))
plt.barh(range(15), scores[top_idx][::-1])
plt.yticks(range(15), feature_names[top_idx][::-1])
plt.xlabel('F-score')
plt.title('Top 15 Features - ANOVA F-test')
plt.tight_layout()
plt.savefig('filter_scores.png', dpi=150)
plt.show()
