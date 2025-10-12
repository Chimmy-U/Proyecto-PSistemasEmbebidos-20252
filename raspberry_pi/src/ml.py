import os
import numpy as np
import tensorflow as tf

tflite = tf.lite

MODEL_PATH = "C:/Users/Miguel/Desktop/U/Semestre 2025-2/PROFU I/PROJECT_S/data/models/sound_classifier.tflite"

# Orden de características (debe coincidir con el entrenamiento)
FEATURE_NAMES = [
    'rms_value', 'rms_avg', 'rms_std', 'is_day',
    'weather_con llovizna', 'weather_con niebla', 'weather_con tormentas',
    'weather_lloviendo', 'weather_llovizna',
    'weather_parcialmente nublado', 'weather_soleado'
]


# Valores mínimos y máximos del entrenamiento (para normalización)
FEATURE_MIN = {
    'rms_value': 1.0, 'rms_avg': 1.7, 'rms_std': 0.0, 'is_day': 0.0,
    'weather_con llovizna': 0.0, 'weather_con niebla': 0.0, 'weather_con tormentas': 0.0,
    'weather_lloviendo': 0.0, 'weather_llovizna': 0.0,
    'weather_parcialmente nublado': 0.0, 'weather_soleado': 0.0
}

FEATURE_MAX = {
    'rms_value': 8572.0, 'rms_avg': 5529.1, 'rms_std': 2428.442090907025, 'is_day': 1.0,
    'weather_con llovizna': 1.0, 'weather_con niebla': 1.0, 'weather_con tormentas': 1.0,
    'weather_lloviendo': 1.0, 'weather_llovizna': 1.0,
    'weather_parcialmente nublado': 1.0, 'weather_soleado': 1.0
}


if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"No se encontró el modelo TFLite en: {MODEL_PATH}")


# Cargar modelo TFLite
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

INPUT_DETAILS = interpreter.get_input_details()
OUTPUT_DETAILS = interpreter.get_output_details()

def _normalize_value(name, value):
    """Normaliza escalar entre 0 y 1 usando min/max conocidos."""
    mn = FEATURE_MIN[name]
    mx = FEATURE_MAX[name]
    denom = (mx - mn) if (mx - mn) != 0 else 1.0
    return (value - mn) / denom


def _list_to_vector(lst):
    """Convierte lista en vector normalizado en el orden de FEATURE_NAMES."""
    if len(lst) != len(FEATURE_NAMES):
        raise ValueError(f"La lista debe tener {len(FEATURE_NAMES)} elementos (recibidos {len(lst)}).")
    normed = [_normalize_value(FEATURE_NAMES[i], float(lst[i])) for i in range(len(FEATURE_NAMES))]
    return np.array(normed, dtype=np.float32)


# Predicción
def predict_sound_category(values_list):
    """
    Recibe una lista de valores en el mismo orden de FEATURE_NAMES.
    Devuelve el índice (int) de la categoría predicha.
    """
    vec = _list_to_vector(values_list)
    x = np.expand_dims(vec, axis=0).astype(np.float32)
    interpreter.set_tensor(INPUT_DETAILS[0]['index'], x)
    interpreter.invoke()
    out = interpreter.get_tensor(OUTPUT_DETAILS[0]['index'])
    probs = np.squeeze(out)
    pred_idx = int(np.argmax(probs))
    return pred_idx


# RMS Values
from collections import deque
RMS_WINDOW_SIZE = 10
_rms_buffer = deque(maxlen=RMS_WINDOW_SIZE)

def update_rms_and_get_stats(rms_value):
    """
    Añade rms_value al buffer interno y devuelve (rms_avg, rms_std).
    """
    try:
        v = float(rms_value)
    except Exception:
        v = 0.0
    _rms_buffer.append(v)
    arr = list(_rms_buffer)
    if not arr:
        return float(v), 0.0
    avg = sum(arr) / len(arr)
    mean = avg
    var = sum((x - mean) ** 2 for x in arr) / len(arr)
    std = var ** 0.5
    return float(avg), float(std)


# Mapeo de weather (status_weather es [day_string, weather_string])
def _normalize_is_day(day_string):
    """
    Recibe day_string y devuelve 0/1.
    """
    if day_string is None:
        return 0
    s = str(day_string).strip().lower()
    if s in ('día'):
        return 1
    return 0

def _weather_name_to_flags(name_string):
    """
    Name_string es un string con el tipo de clima (p.ej. 'Parcialmente nublado', 'Lluvia ligera').
    Devuelve un dict con los 7 flags que usa el modelo.
    """
    flags = {
        'weather_con llovizna': 0,
        'weather_con niebla': 0,
        'weather_con tormentas': 0,
        'weather_lloviendo': 0,
        'weather_llovizna': 0,
        'weather_parcialmente nublado': 0,
        'weather_soleado': 0
    }

    n = (name_string or '').strip().lower()

    mapping = {
        'soleado': 'weather_soleado',
        'parcialmente nublado': 'weather_parcialmente nublado',
        'con niebla': 'weather_con niebla',
        'con llovizna': 'weather_con llovizna',
        'lloviendo': 'weather_lloviendo',
        'con tormentas': 'weather_con tormentas'
        # 'desconocido' simplemente no activa ningún flag
    }

    if n in mapping:
        flags[mapping[n]] = 1

    return flags

def build_feature_list(rms_value, status_weather):
    """
    Devuelve la lista de 11 floats en el orden de FEATURE_NAMES.
    """
    # 1) stats a partir de RMS
    rms_avg, rms_std = update_rms_and_get_stats(rms_value)

    # 2) status_weather -> is_day + weather name
    try:
        day_string = status_weather[0]
        weather_string = status_weather[1]
    except Exception:
        day_string = ''
        weather_string = ''

    is_day_flag = _normalize_is_day(day_string)
    weather_flags = _weather_name_to_flags(weather_string)

    # 3) construir lista en orden
    values = [
        float(rms_value),
        float(rms_avg),
        float(rms_std),
        float(is_day_flag),
        float(weather_flags['weather_con llovizna']),
        float(weather_flags['weather_con niebla']),
        float(weather_flags['weather_con tormentas']),
        float(weather_flags['weather_lloviendo']),
        float(weather_flags['weather_llovizna']),
        float(weather_flags['weather_parcialmente nublado']),
        float(weather_flags['weather_soleado'])
    ]
    return values