# Aula 4 — Slide 14 — MATRIZ DE CONFUSÃO: IMPLEMENTAÇÃO

from sklearn.metrics import confusion_matrix, classification_report
from sklearn.ensemble import RandomForestClassifier
import seaborn as sns

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# Matriz de Confusão
cm = confusion_matrix(y_test, y_pred)

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='RdPu',
            xticklabels=['Neg', 'Pos'],
            yticklabels=['Neg', 'Pos'])
plt.xlabel('Previsto')
plt.ylabel('Real')
plt.title('Matriz de Confusão')
plt.savefig('confusion_matrix.png', dpi=150)

# Classification Report completo
print(classification_report(y_test, y_pred,
      target_names=['Negativo', 'Positivo']))
