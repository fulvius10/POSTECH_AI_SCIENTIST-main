# Aula 4 — Slide 51 — MONITORANDO PERFORMANCE

# Monitoramento contínuo de performance em produção
import pandas as pd

def monitor_performance(model, X_batches, y_batches, threshold=0.7):
    """Monitora AUC a cada batch de dados novos"""
    history = []

    for i, (X_batch, y_batch) in enumerate(zip(X_batches, y_batches)):
        y_proba = model.predict_proba(X_batch)[:, 1]
        auc = roc_auc_score(y_batch, y_proba)

        history.append({'batch': i, 'auc': auc, 'n_samples': len(y_batch)})

        if auc < threshold:
            print(f'⚠️ ALERTA Batch {i}: AUC={auc:.4f} < {threshold}')
            print(f'   → Considere retreinar o modelo!')
        else:
            print(f'✅ Batch {i}: AUC={auc:.4f}')

    return pd.DataFrame(history)
