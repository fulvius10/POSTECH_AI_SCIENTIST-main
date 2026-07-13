# Aula 5 — Slide 35 — EARLY STOPPING

from tensorflow.keras.callbacks import EarlyStopping

early_stop = EarlyStopping(
    monitor='val_loss',     # métrica monitorada
    patience=10,            # espera 10 epochs sem melhora
    restore_best_weights=True  # restaura pesos do melhor epoch
)

history = model_nn.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=500,             # máximo de epochs
    callbacks=[early_stop],
    verbose=1
)
print(f'Parou no epoch: {early_stop.stopped_epoch}')
print(f'Melhor val_loss: {min(history.history["val_loss"]):.4f}')
