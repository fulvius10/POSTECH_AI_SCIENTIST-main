# Aula 4 — Slide 32 — IMPLEMENTAÇÃO: SÉRIE TEMPORAL SINTÉTICA

import pandas as pd
import numpy as np

np.random.seed(42)
n_days = 365 * 2
dates = pd.date_range('2022-01-01', periods=n_days, freq='D')
trend = np.linspace(100, 150, n_days)
sales = (trend
    + 20 * np.sin(2*np.pi*np.arange(n_days)/365)    # sazonalidade anual
    + 10 * np.sin(2*np.pi*np.arange(n_days)/7)       # sazonalidade semanal
    + np.random.normal(0, 5, n_days))                 # ruído

df = pd.DataFrame({'date': dates, 'sales': sales})

# Features temporais
for lag in [1, 7, 14, 30]:
    df[f'lag_{lag}'] = df['sales'].shift(lag)
df['rolling_7'] = df['sales'].shift(1).rolling(7).mean()
df['dow'] = df['date'].dt.dayofweek
df['month'] = df['date'].dt.month
df = df.dropna().reset_index(drop=True)

feat_cols = [c for c in df.columns if c not in ['date','sales']]
X, y = df[feat_cols].values, df['sales'].values
print(f'Shape: {X.shape}, Features: {feat_cols}')
