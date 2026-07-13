# Aula 5 — Slide 34 — DROPOUT

# Dropout em MLP do Scikit-Learn (não tem dropout nativo)
# Usando Keras/TensorFlow:
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout

model_nn = Sequential([
    Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.3),        # ← 30% dos neurônios desativados
    Dense(64, activation='relu'),
    Dropout(0.2),        # ← 20% dos neurônios desativados
    Dense(1, activation='sigmoid')
])
model_nn.compile(optimizer='adam', loss='binary_crossentropy',
                 metrics=['accuracy'])
