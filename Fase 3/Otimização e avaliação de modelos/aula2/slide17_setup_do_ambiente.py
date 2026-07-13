# Aula 2 — Slide 17 — SETUP DO AMBIENTE

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import (
    train_test_split, GridSearchCV, RandomizedSearchCV,
    StratifiedKFold, cross_val_score
)
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import optuna
from scipy.stats import uniform, randint

# Dataset sintético: 20 features (15 informativas + 5 redundantes)
X, y = make_classification(
    n_samples=1000, n_features=20,
    n_informative=15, n_redundant=5, random_state=42
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)
print(f'Treino: {X_train.shape} | Teste: {X_test.shape}')
