# Aula 5 — Slide 14 — LEARNING CURVES

from sklearn.model_selection import learning_curve
import numpy as np

train_sizes, train_scores, val_scores = learning_curve(
    model, X_train, y_train, cv=5,
    train_sizes=np.linspace(0.1, 1.0, 10),
    scoring='neg_mean_squared_error', n_jobs=-1
)

train_mean = -train_scores.mean(axis=1)
val_mean = -val_scores.mean(axis=1)

plt.figure(figsize=(10, 6))
plt.plot(train_sizes, train_mean, label='Treino', color='#4CAF50')
plt.plot(train_sizes, val_mean, label='Validação', color='#D30F59')
plt.fill_between(train_sizes, train_mean, val_mean, alpha=0.1, color='red')
plt.xlabel('Tamanho do Treino')
plt.ylabel('Erro (MSE)')
plt.legend()
plt.title('Learning Curve')
plt.savefig('learning_curve.png', dpi=150)
