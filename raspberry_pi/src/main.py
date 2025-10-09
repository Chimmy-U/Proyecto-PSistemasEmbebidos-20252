"""
Aplicación principal Raspberry Pi - Sistema de Agente IA
Maneja MQTT, consultas API, Machine Learning y toma de decisiones
"""

import time
import threading
import mqtt_host
import api
import random

def weather_loop():
    while True:
        status_weather = api.get_weather_status()
        print(status_weather)
        time.sleep(10)

def mqtt_listener_loop():
    while True:
        try:
            msg = mqtt_host.get_latest_message()
            if msg is not None:
                mqtt_host.latest_message = None
            time.sleep(0.2)
        except Exception as e:
            print(f"[ERROR - MQTT] {e}")
            time.sleep(2)


def main():

    client = mqtt_host.start_mqtt()

    weather_thread = threading.Thread(target=weather_loop, daemon=True)
    weather_thread.start()

    mqtt_thread = threading.Thread(target=mqtt_listener_loop, daemon=True)
    mqtt_thread.start()

    try:
        # Bucle principal
        while True:
            random_number = random.randint(0, 3)
            mqtt_host.publish_to_esp32(str(random_number))
            time.sleep(1) 

    except KeyboardInterrupt:
        print("\n🛑 Finalizando...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
