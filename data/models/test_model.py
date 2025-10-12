
"""
predict_tflite.py
Ejemplo de uso de tflite_runtime.Interpreter para tu modelo sound_classifier.tflite.
"""

import os
import numpy as np
import tensorflow as tf
tflite = tf.lite


MODEL_FILENAME = "sound_classifier.tflite"

# Orden de features (exactamente igual al entrenamiento)
feature_names = [
    'rms_value', 'rms_avg', 'rms_std', 'is_day',
    'weather_con llovizna', 'weather_con niebla', 'weather_con tormentas',
    'weather_lloviendo', 'weather_llovizna',
    'weather_parcialmente nublado', 'weather_soleado'
]

# Min / Max del entrenamiento (para normalizar)
feature_min = {
    'rms_value': 1.0, 'rms_avg': 1.7, 'rms_std': 0.0, 'is_day': 0.0,
    'weather_con llovizna': 0.0, 'weather_con niebla': 0.0, 'weather_con tormentas': 0.0,
    'weather_lloviendo': 0.0, 'weather_llovizna': 0.0,
    'weather_parcialmente nublado': 0.0, 'weather_soleado': 0.0
}
feature_max = {
    'rms_value': 8572.0, 'rms_avg': 5529.1, 'rms_std': 2428.442090907025, 'is_day': 1.0,
    'weather_con llovizna': 1.0, 'weather_con niebla': 1.0, 'weather_con tormentas': 1.0,
    'weather_lloviendo': 1.0, 'weather_llovizna': 1.0,
    'weather_parcialmente nublado': 1.0, 'weather_soleado': 1.0
}

# Mapping índice -> etiqueta
class_map = {
    0: "Actividad moderada",
    1: "Ambiente tranquilo",
    2: "Pico inesperado",
    3: "Ruido elevado"
}

script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, MODEL_FILENAME)

if not os.path.exists(model_path):
    raise FileNotFoundError(f"No se encontró el modelo TFLite en: {model_path}")

interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def normalize_value(name, value):
    """Normaliza escalar entre 0 y 1 usando min/max conocidos."""
    mn = feature_min[name]
    mx = feature_max[name]
    denom = (mx - mn) if (mx - mn) != 0 else 1.0
    return (value - mn) / denom

def dict_to_vector(d):
    """Convierte dict (o mapping) de features en vector normalizado."""
    vec = [normalize_value(fname, float(d[fname])) for fname in feature_names]
    return np.array(vec, dtype=np.float32)

def list_to_vector(lst):
    """Convierte lista en vector (asume el orden de feature_names)."""
    if len(lst) != len(feature_names):
        raise ValueError(f"Lista debe tener {len(feature_names)} elementos.")
    return np.array([normalize_value(feature_names[i], float(lst[i])) for i in range(len(lst))], dtype=np.float32)


# Funciones de predicción

def predict_from_vector(vec):
    x = np.array([vec], dtype=np.float32)
    interpreter.set_tensor(input_details[0]['index'], x)
    interpreter.invoke()
    out = interpreter.get_tensor(output_details[0]['index'])
    probs = np.squeeze(out)
    pred_idx = int(np.argmax(probs))
    pred_label = class_map.get(pred_idx, str(pred_idx))
    return pred_idx, pred_label, probs

def predict_from_dict(d):
    return predict_from_vector(dict_to_vector(d))

def predict_from_list(lst):
    return predict_from_vector(list_to_vector(lst))

# Ejemplos / pruebas

if __name__ == "__main__":
    # Ejemplo con dict (valores no normalizados)
    sample = {
        'rms_value': 3000,
        'rms_avg': 1000,
        'rms_std': 500,
        'is_day': 1.0,
        'weather_con llovizna': 0,
        'weather_con niebla': 0,
        'weather_con tormentas': 0,
        'weather_lloviendo': 0,
        'weather_llovizna': 0,
        'weather_parcialmente nublado': 0,
        'weather_soleado': 1
    }

    idx, label, probs = predict_from_dict(sample)
    print("\nEjemplo (dict) -> idx:", idx, "label:", label)
    print("Probabilidades:", probs)

    # Ejemplo con lista (orden debe coincidir con feature_names)
    lst = [3000, 1000, 500, 1, 0, 0, 0, 0, 0, 0, 1]
    idx2, label2, probs2 = predict_from_list(lst)
    print("\nEjemplo (lista) -> idx:", idx2, "label:", label2)
    print("Probabilidades:", probs2)
