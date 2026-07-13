# Aula 1 — Slide 60 — COMPARAÇÃO FINAL:

results = {}
for name, Xtr, Xte in [
    ('Filter (ANOVA)', X_tr_filt, X_te_filt),
    ('Wrapper (RFE)',  X_tr_wrap, X_te_wrap),
    ('Embedded (RF)',  X_tr_emb,  X_te_emb),
    ('Embedded (L1)',  X_tr_l1,   X_te_l1),
]:
    clf = LogisticRegression(max_iter=10000)
    clf.fit(Xtr, y_train)
    acc = accuracy_score(y_test, clf.predict(Xte))
    results[name] = acc
    print(f'{name:20s} → Acurácia: {acc:.4f}')

import time
for name, sel_func in methods:
    start = time.time()
    sel_func.fit(X_train_sc, y_train)
    elapsed = time.time() - start
    print(f'{name:20s} → Tempo: {elapsed:.3f}s')
