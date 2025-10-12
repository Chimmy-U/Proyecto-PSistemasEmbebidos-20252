"""dataset_generator.py
Lee un archivo, calcula
características móviles (rms_avg, rms_std) y escribe un CSV de salida con
las siguientes columnas:

rms_value, rms_avg, rms_std, is_day, weather_type, sound_category

"""
from pathlib import Path
import pandas as pd


def rolling_features(rms_series, window):
    avg = rms_series.rolling(window=window, min_periods=1).mean()
    std = rms_series.rolling(window=window, min_periods=1).std().fillna(0.0)
    return avg, std


HERE = Path(__file__).resolve().parent
INPUT_FILENAME = HERE / "data.csv"
OUTPUT_FILENAME = HERE / "dataset.csv"
WINDOW = 10


def ensure_columns(df: pd.DataFrame):
    """Asegura que existan las columnas demandadas en el dataframe.

    Si faltan, se añaden con valores por defecto:
      - is_day: 0
      - weather_type: 'unknown'
      - sound_category: 'unknown'
    """
    defaults = {
        "is_day": 0,
        "weather_type": "unknown",
        "sound_category": "unknown",
    }

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    return df


def main():
    # Leer input
    if not INPUT_FILENAME.exists():
        raise SystemExit(f"ERROR: no se encontró {INPUT_FILENAME}")

    df = pd.read_csv(INPUT_FILENAME)

    if "rms_value" not in df.columns:
        raise SystemExit("ERROR: el CSV debe contener la columna 'rms_value'.")

    # Normalizar rms_value a numérico
    df["rms_value"] = pd.to_numeric(df["rms_value"], errors="coerce").fillna(0.0)

    # Asegurar columnas adicionales
    df = ensure_columns(df)

    # Calcular características móviles
    df["rms_avg"], df["rms_std"] = rolling_features(df["rms_value"], WINDOW)

    # Seleccionar y ordenar columnas de salida según lo pedido
    out_cols = ["rms_value", "rms_avg", "rms_std", "is_day", "weather_type", "sound_category"]

    # Si existieran columnas extra en el CSV original, se ignoran en la salida
    out_df = df.reindex(columns=out_cols)

    out_df.to_csv(OUTPUT_FILENAME, index=False)
    print(f"Dataset escrito en: {OUTPUT_FILENAME}")
    print("Columnas de salida:", ", ".join(out_df.columns))


if __name__ == "__main__":
    main()
