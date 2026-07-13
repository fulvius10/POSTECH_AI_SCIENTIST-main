# Aula 1 — Slide 30 — TESTE QUI-QUADRADO (CHI-SQUARED)

from sklearn.feature_selection import SelectKBest, chi2
from sklearn.preprocessing import MinMaxScaler

# Chi2 requer valores não-negativos
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X_train)

sel = SelectKBest(chi2, k=10)
X_selected = sel.fit_transform(X_scaled, y_train)
print('Features selecionadas:', sel.get_support(indices=True))
