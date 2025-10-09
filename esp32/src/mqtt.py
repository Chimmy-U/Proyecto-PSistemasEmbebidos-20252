
import network
import time
from umqtt.simple import MQTTClient
import secrets

latest_message = None

def on_message(topic, msg):
    global latest_message
    print(f" Mensaje recibido en {topic.decode()}: {msg.decode()}")
    latest_message = msg.decode()

def wifi_connect():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        print("Conectando a WiFi...")
        sta.connect(secrets.WIFI_SSID, secrets.WIFI_PSK)
        while not sta.isconnected():
            print(".", end="")
            time.sleep(0.5)
    print("\nWiFi conectado:", sta.ifconfig())

def mqtt_connect():
    client = MQTTClient(secrets.CLIENT_ID, secrets.BROKER)
    client.set_callback(on_message)
    client.connect()
    print("MQTT conectado al broker:", secrets.BROKER)
    return client

def mqtt_publish(client, message):
    if isinstance(message, str):
        message = message.encode()  # Convertir a bytes si es texto
    client.publish(secrets.TOPIC_MIC, message)
    print(f"Publicado en {secrets.TOPIC_MIC.decode()}: {message}")



def mqtt_subscribe(client):
    client.subscribe(secrets.TOPIC_LED)

def check_messages(client):
    client.check_msg()