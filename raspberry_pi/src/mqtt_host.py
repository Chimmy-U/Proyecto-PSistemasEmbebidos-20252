import paho.mqtt.client as mqtt
import secrets


latest_message = None

def on_message(client, userdata, msg):
    global latest_message
    message = msg.payload.decode()
    print(f"Mensaje recibido en {msg.topic}: {message}")
    latest_message = message

def start_mqtt():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(secrets.BROKER, secrets.PORT, 60)
    client.subscribe(secrets.TOPIC_MIC)

    client.loop_start()
    return client

def get_latest_message():
    global latest_message
    return latest_message


def publish_to_esp32(message):
    client = mqtt.Client()
    client.connect(secrets.BROKER, secrets.PORT, 60)
    client.publish(secrets.TOPIC_LED, message)
    client.disconnect()
    print(f"Publicado en {secrets.TOPIC_LED}: {message}")
