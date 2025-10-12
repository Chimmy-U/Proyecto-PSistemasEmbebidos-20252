"""
Archivo principal ESP32 - Sistema de Agente IA
Maneja micrófono, LEDs y comunicación MQTT
"""

from rgb import RGBLed
from inmp import INMP441
import mqtt
import time

# Pines
R = 4
G = 17
B = 16
SCK = 14
WS  = 15
SD  = 32

# Instancias
leds = RGBLed(R,G,B)
mic = INMP441(SCK, WS, SD)

def main():

    mqtt.wifi_connect()
    client = mqtt.mqtt_connect()
    mqtt.mqtt_subscribe(client)

    try:
        while True:
            rms = mic.read_sample()

            mqtt.mqtt_publish(client, str(rms))

            mqtt.check_messages(client)
            if mqtt.latest_message is not None:
                response = mqtt.latest_message

                if response == "0":
                    leds.yellow()
                elif response == "1":
                    leds.green()
                elif response == "2":
                    leds.blue()
                elif response == "3":
                    leds.red()
                else:
                    leds.off()

                mqtt.latest_message = None

            time.sleep(0.2)

    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()
        print("MQTT desconectado.")



# Ejecutar main
if __name__ == "__main__":
    main()