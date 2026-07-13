# Aula 4 — Slide 49 — DETECTANDO DATA DRIFT

from scipy.stats import ks_2samp
import numpy as np

# Comparar distribuição de treino vs produção
def detect_drift(train_data, prod_data, threshold=0.05):
    results = {}
    for col in range(train_data.shape[1]):
        stat, pvalue = ks_2samp(train_data[:, col], prod_data[:, col])
        results[f'feature_{col}'] = {
            'ks_stat': stat,
            'p_value': pvalue,
            'drift': pvalue < threshold
        }
    return results

# Simular dados de produção com drift
X_prod = X_test + np.random.normal(0.5, 0.1, X_test.shape)  # drift!

drift_results = detect_drift(X_train, X_prod)
drifted = [k for k,v in drift_results.items() if v['drift']]
print(f'Features com drift: {len(drifted)} de {X_train.shape[1]}')
