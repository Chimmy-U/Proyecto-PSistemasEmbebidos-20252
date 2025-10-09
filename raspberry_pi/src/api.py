import requests
import datetime

# Coordenadas de Armenia, Quindío (aprox)
LAT = 4.3270
LON = 75.4120

def get_weather_status():
    """
    Consulta Open-Meteo y devuelve un resumen:
    - Si es de día o noche
    - Estado general del clima
    """
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={LAT}"
            f"&longitude={LON}"
            "&current_weather=true"
            "&daily=sunrise,sunset"
            "&timezone=America/Bogota"
        )
        r = requests.get(url, timeout=10)
        data = r.json()

        current = data["current_weather"]
        daily = data["daily"]

        # Offset horario local (ej. -18000 seg = -5h)
        offset = datetime.timedelta(seconds=data["utc_offset_seconds"])

        # Convertir a datetime con zona local
        now = datetime.datetime.fromisoformat(current["time"]) + offset
        sr = datetime.datetime.fromisoformat(daily["sunrise"][0]) + offset
        ss = datetime.datetime.fromisoformat(daily["sunset"][0]) + offset

        moment = "día" if sr <= now < ss else "noche"
        state = interpret_weathercode(current["weathercode"])

        return moment, state

    except Exception as e:
        return f"Error al obtener clima: {e}"

def interpret_weathercode(code):
    """
    Traduce los códigos de Open-Meteo a texto legible.
    """
    if code in (0,):
        return "soleado"
    elif code in (1, 2, 3):
        return "parcialmente nublado"
    elif code in (45, 48):
        return "con niebla"
    elif code in (51, 53, 55, 56, 57):
        return "con llovizna"
    elif code in (61, 63, 65, 80, 81, 82):
        return "lloviendo"
    elif code in (71, 73, 75, 77, 85, 86):
        return "nevando"
    elif code in (95, 96, 99):
        return "con tormentas"
    else:
        return "desconocido"
