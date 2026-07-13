# Aula 4 — Slide 12 — TRADE-OFF PRECISÃO × RECALL

from sklearn.metrics import precision_recall_curve
import matplotlib.pyplot as plt

# Probabilidades do modelo
y_proba = model.predict_proba(X_test)[:, 1]

# Curva Precision-Recall
prec, rec, thresholds = precision_recall_curve(y_test, y_proba)

plt.figure(figsize=(8, 5))
plt.plot(rec, prec, color='#D30F59', linewidth=2)
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Curva Precision-Recall')
plt.grid(alpha=0.3)
plt.savefig('pr_curve.png', dpi=150)
plt.show()
