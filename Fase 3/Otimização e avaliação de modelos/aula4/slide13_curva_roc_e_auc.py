# Aula 4 — Slide 13 — CURVA ROC E AUC

from sklearn.metrics import roc_curve, roc_auc_score

y_proba = model.predict_proba(X_test)[:, 1]
fpr, tpr, thresholds = roc_curve(y_test, y_proba)
auc = roc_auc_score(y_test, y_proba)

plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='#D30F59', linewidth=2,
         label=f'ROC (AUC = {auc:.4f})')
plt.plot([0,1], [0,1], 'k--', alpha=0.3, label='Aleatório')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate (Recall)')
plt.title('Curva ROC')
plt.legend()
plt.savefig('roc_curve.png', dpi=150)
