"""
Aplicación principal Raspberry Pi - Sistema de Agente IA
Maneja MQTT, consultas API, Machine Learning y toma de decisiones
"""

import time
import threading
import mqtt_host
import api
from ml import predict_sound_category, build_feature_list
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="tensorflow")

latest_rms_value = None
latest_weather = None

def weather_loop():
    global latest_weather
    while True:
        try:
            latest_weather = api.get_weather_status()  # [is_day_str, weather_name]
        except Exception as e:
            print(f"[ERROR - Weather] {e}")
        time.sleep(10)

def mqtt_listener_loop():
    global latest_rms_value
    while True:
        try:
            msg = mqtt_host.get_latest_message()
            if msg is not None:
                latest_rms_value = msg
                mqtt_host.latest_message = None
        except Exception as e:
            print(f"[ERROR - MQTT] {e}")
        time.sleep(0.2)


def main():

    client = mqtt_host.start_mqtt()

    weather_thread = threading.Thread(target=weather_loop, daemon=True)
    weather_thread.start()

    mqtt_thread = threading.Thread(target=mqtt_listener_loop, daemon=True)
    mqtt_thread.start()

    global latest_rms_value, latest_weather

    try:
        # Bucle principal
        while True:

            if latest_rms_value is None or latest_weather is None:
                # Aún no se han recibido datos
                time.sleep(0.5)
                continue

            data = build_feature_list(latest_rms_value, latest_weather)

            print(f"Datos: {data}")

            pred = predict_sound_category(data)

            mqtt_host.publish_to_esp32(str(pred))

            time.sleep(1) 

    except KeyboardInterrupt:
        print("\n🛑 Finalizando...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
