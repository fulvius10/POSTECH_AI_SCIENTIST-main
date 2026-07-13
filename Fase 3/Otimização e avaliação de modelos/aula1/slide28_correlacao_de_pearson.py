# Aula 1 — Slide 28 — CORRELAÇÃO DE PEARSON

import pandas as pd
from sklearn.datasets import load_breast_cancer

data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(data.target)

# Correlação de Pearson com o alvo
corr = X.corrwith(y).abs().sort_values(ascending=False)
print(corr.head(10))
