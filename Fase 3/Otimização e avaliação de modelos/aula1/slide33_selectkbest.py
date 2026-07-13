# Aula 1 — Slide 33 — SELECTKBEST

from sklearn.feature_selection import SelectKBest, f_classif, chi2
from sklearn.feature_selection import mutual_info_classif

# Opção 1: ANOVA F-test (variáveis contínuas → alvo categórico)
sel_anova = SelectKBest(f_classif, k=10)
X_anova = sel_anova.fit_transform(X_train_sc, y_train)

# Opção 2: Chi-Squared (variáveis categóricas)
sel_chi2 = SelectKBest(chi2, k=10)

# Opção 3: Mutual Information
sel_mi = SelectKBest(mutual_info_classif, k=10)

# Verificar quais features foram selecionadas
selected_names = X.columns[sel_anova.get_support()]
print('Top 10 features (ANOVA):', selected_names.tolist())
