# Algorithm 2 (Training) - DNN Fall Prediction in cStick 2.0
# Architecture & training params match the paper.

import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers

# -----------------------------
# Data loading (replace with your real CSV path)
# Expected columns (example):
#   a, g, hrv, bs, sp, d, label
# label in {0,1,2}
# -----------------------------
DATA_CSV = Path("fall_dataset.csv")  # <-- change
df = pd.read_csv(DATA_CSV)

feature_cols = ["a", "g", "hrv", "bs", "sp", "d"]
X = df[feature_cols].values.astype(np.float32)
y = df["label"].values.astype(np.int64)

# -----------------------------
# Step 2: Preprocessing (normalize) + split 7736/1934
# The exact split counts occur when dataset=9670.
# We enforce test_size to match 1934/9670 when possible.
# -----------------------------
test_size = 1934 / 9670  # ~0.2
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=test_size, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# -----------------------------
# Step 3: DNN architecture
# - Input: 6
# - Dense(20, ReLU)
# - Dense(20, ReLU)
# - Dense(3, Softmax)
# -----------------------------
model = models.Sequential([
    layers.Input(shape=(6,)),
    layers.Dense(20, activation="relu"),
    layers.Dense(20, activation="relu"),
    layers.Dense(3, activation="softmax"),
])

# -----------------------------
# Step 4: Training parameters
# - SGD, lr=0.01
# - epochs=200
# - batch_size=32
# -----------------------------
opt = optimizers.SGD(learning_rate=0.01)

model.compile(
    optimizer=opt,
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

history = model.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=200,
    batch_size=32,
    verbose=1
)

# Evaluate
pred = np.argmax(model.predict(X_test), axis=1)
print("Confusion Matrix:\n", confusion_matrix(y_test, pred))
print(classification_report(y_test, pred))

# Save artifacts for edge use
model.save("cstick_dnn_tf")
np.save("scaler_mean.npy", scaler.mean_)
np.save("scaler_scale.npy", scaler.scale_)
print("Saved model + scaler.")