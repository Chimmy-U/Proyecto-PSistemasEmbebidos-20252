
"""
model_trainer_embedded.py
Entrena un modelo de clasificación de ambientes sonoros a partir de un dataset CSV.

Entradas:
  - rms_value: valor RMS del sonido capturado.
  - rms_avg: promedio móvil del RMS.
  - rms_std: desviación estándar del RMS.
  - is_day: 'día' o 'noche'.
  - weather_type: tipo de clima (soleado, lluvioso, etc.).

Salida:
  - sound_category: categoría del ambiente sonoro
    ('Ambiente tranquilo', 'Actividad moderada', 'Ruido elevado', 'Pico inesperado').

"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


def prepare_inputs(df: pd.DataFrame):
    """Selecciona y convierte las columnas de entrada."""
    cols = ['rms_value', 'rms_avg', 'rms_std', 'is_day', 'weather_type']
    for c in cols:
        if c not in df.columns:
            raise ValueError(f"Columna faltante en dataset: {c}")

    X = df[cols].copy()

    # Convertir is_day a numérico (día=1, noche=0)
    X['is_day'] = X['is_day'].astype(str).str.lower().map(
        {'día': 1, 'dia': 1, 'noche': 0}
    ).fillna(0).astype(float)

    # One-hot encoding de weather_type
    dummies = pd.get_dummies(X['weather_type'].fillna('unknown').astype(str),
                             prefix='weather')
    X = X.drop(columns=['weather_type'])
    X = pd.concat([X.reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)

    # Asegurar que todas las columnas sean numéricas
    X = X.apply(pd.to_numeric, errors='coerce')
    return X


def build_model(input_dim, num_classes):
    """Crea una red neuronal totalmente conectada."""
    model = keras.Sequential([
        layers.Input(shape=(input_dim,)),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(32, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation='softmax')
    ])
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def train_model(csv_path: str):
    """Carga el dataset, entrena el modelo y exporta los archivos."""
    print(f"\n📂 Cargando dataset desde: {csv_path}")
    df = pd.read_csv(csv_path)

    if 'sound_category' not in df.columns:
        raise ValueError("El dataset debe contener la columna 'sound_category'.")

    # Separar entradas (X) y etiquetas (y)
    X_df = prepare_inputs(df)
    y_raw = df['sound_category'].astype(str).fillna('unknown')

    # Imputar valores faltantes (media)
    imputer = SimpleImputer(strategy='mean')
    X_imp = pd.DataFrame(imputer.fit_transform(X_df), columns=X_df.columns)

    # Codificar etiquetas
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    class_map = {cls: int(idx) for idx, cls in enumerate(le.classes_)}

    # Dividir en entrenamiento y validación (80/20)
    X_train, X_val, y_train, y_val = train_test_split(
        X_imp.values, y, test_size=0.2, random_state=42, stratify=y
    )

    # Escalar entre 0 y 1
    scaler = MinMaxScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    # Crear modelo
    model = build_model(X_train.shape[1], len(le.classes_))

    # Entrenamiento con early stopping
    es = keras.callbacks.EarlyStopping(
        patience=10, restore_best_weights=True, monitor='val_loss'
    )

    print("\n🚀 Entrenando modelo...\n")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=300,
        batch_size=64,
        callbacks=[es],
        verbose=2
    )

    # Evaluar
    loss, acc = model.evaluate(X_val, y_val, verbose=0)
    print(f"\n✅ Entrenamiento completo: loss={loss:.4f}, acc={acc:.4f}")

    # Guardar modelo .h5
    keras_path = "sound_classifier.h5"
    model.save(keras_path)
    print(f"💾 Modelo Keras guardado en: {keras_path}")

    # Convertir a TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    tflite_path = "sound_classifier.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"💾 Modelo TFLite guardado en: {tflite_path}")

    # Mostrar información útil para inferencia
    print("\n--- Información para inferencia ---")
    mins = dict(zip(X_df.columns, scaler.data_min_.tolist()))
    maxs = dict(zip(X_df.columns, scaler.data_max_.tolist()))
    print("Feature min (train):", mins)
    print("Feature max (train):", maxs)
    print("Class mapping (label -> index):", class_map)
    print("\nUsa los valores min/max para normalizar las entradas antes de predecir en un dispositivo embebido.")

    return model, le, scaler


if __name__ == "__main__":
    train_model("C:/Users/Miguel/Desktop/U/Semestre 2025-2/PROFU I/PROJECT_S/data/datasets/dataset.csv")
