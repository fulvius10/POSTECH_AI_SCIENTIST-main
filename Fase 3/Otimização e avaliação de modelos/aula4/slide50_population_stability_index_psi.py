# Aula 4 — Slide 50 — POPULATION STABILITY INDEX (PSI)

def psi(expected, actual, bins=10):
    """Population Stability Index"""
    # Discretizar em bins
    breakpoints = np.percentile(expected, np.linspace(0, 100, bins+1))
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    expected_pct = np.histogram(expected, breakpoints)[0] / len(expected)
    actual_pct = np.histogram(actual, breakpoints)[0] / len(actual)

    # Evitar log(0)
    expected_pct = np.clip(expected_pct, 0.001, None)
    actual_pct = np.clip(actual_pct, 0.001, None)

    return np.sum((actual_pct - expected_pct) *
                  np.log(actual_pct / expected_pct))

# PSI < 0.1: sem drift | 0.1-0.25: drift moderado | > 0.25: drift severo
for col in range(min(5, X_train.shape[1])):
    score = psi(X_train[:, col], X_prod[:, col])
    status = '✅' if score < 0.1 else ('⚠️' if score < 0.25 else '❌')
    print(f'Feature {col}: PSI={score:.4f} {status}')
