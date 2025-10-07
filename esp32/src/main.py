"""
Archivo principal ESP32 - Sistema de Agente IA
Maneja sensores, actuadores y comunicación MQTT
"""

import network
import time
import ujson
from umqtt.simple import MQTTClient
from machine import Pin, ADC, PWM, Timer
import gc

# Configuración de red y MQTT
WIFI_SSID = "TU_WIFI_SSID"
WIFI_PASSWORD = "TU_WIFI_PASSWORD"
MQTT_BROKER = "192.168.1.100"  # IP de la Raspberry Pi
MQTT_PORT = 1883
CLIENT_ID = "ESP32_001"

# Configuración de pines
LED_STATUS = Pin(2, Pin.OUT)  # LED indicador de estado
LED_MQTT = Pin(4, Pin.OUT)    # LED indicador MQTT

# Sensores (ADC)
TEMP_SENSOR = ADC(Pin(32))    # Sensor de temperatura
HUMIDITY_SENSOR = ADC(Pin(33)) # Sensor de humedad
LIGHT_SENSOR = ADC(Pin(34))   # Sensor de luz
NOISE_SENSOR = ADC(Pin(35))   # Sensor de ruido

# Actuadores (PWM)
FAN_PIN = PWM(Pin(25))        # Ventilador
LED_ACTUATOR = PWM(Pin(26))   # LED controlable
PUMP_PIN = PWM(Pin(27))       # Bomba

# Variables globales
mqtt_client = None
connected = False
last_sensor_reading = 0

def connect_wifi():
    """Conecta a la red WiFi"""
    global connected
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Conectando a WiFi...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            LED_STATUS.value(not LED_STATUS.value())  # Parpadeo durante conexión
            time.sleep(0.5)
            timeout -= 0.5
    
    if wlan.isconnected():
        connected = True
        LED_STATUS.on()
        print('WiFi conectado:', wlan.ifconfig())
        return True
    else:
        connected = False
        LED_STATUS.off()
        print('Error al conectar WiFi')
        return False

def mqtt_callback(topic, msg):
    """Callback para mensajes MQTT recibidos"""
    try:
        topic_str = topic.decode('utf-8')
        message = ujson.loads(msg.decode('utf-8'))
        
        print(f"Mensaje recibido - Tópico: {topic_str}")
        print(f"Contenido: {message}")
        
        # Procesar comandos para actuadores
        if 'actuadores/ventilador' in topic_str:
            control_fan(message)
        elif 'actuadores/led' in topic_str:
            control_led_actuator(message)
        elif 'actuadores/bomba' in topic_str:
            control_pump(message)
        elif 'comandos/emergencia' in topic_str:
            emergency_stop()
            
    except Exception as e:
        print(f"Error procesando mensaje MQTT: {e}")

def connect_mqtt():
    """Conecta al broker MQTT"""
    global mqtt_client
    
    try:
        mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, MQTT_PORT)
        mqtt_client.set_callback(mqtt_callback)
        mqtt_client.connect()
        
        # Suscribirse a tópicos
        mqtt_client.subscribe("proyecto/actuadores/+")
        mqtt_client.subscribe("proyecto/comandos/+")
        
        LED_MQTT.on()
        print("MQTT conectado y suscrito")
        
        # Enviar mensaje de conexión
        status_msg = {
            "device_id": CLIENT_ID,
            "status": "connected",
            "timestamp": time.time()
        }
        mqtt_client.publish("proyecto/estado/esp32/conectado", 
                          ujson.dumps(status_msg))
        
        return True
        
    except Exception as e:
        LED_MQTT.off()
        print(f"Error conectando MQTT: {e}")
        return False

def read_sensors():
    """Lee todos los sensores y retorna un diccionario con los valores"""
    try:
        # Lectura de sensores ADC (0-4095)
        temp_raw = TEMP_SENSOR.read()
        humidity_raw = HUMIDITY_SENSOR.read()
        light_raw = LIGHT_SENSOR.read()
        noise_raw = NOISE_SENSOR.read()
        
        # Conversión a valores reales (ajustar según sensores específicos)
        temperature = (temp_raw / 4095) * 50  # 0-50°C
        humidity = (humidity_raw / 4095) * 100  # 0-100%
        light = (light_raw / 4095) * 1000  # 0-1000 lux
        noise = (noise_raw / 4095) * 100  # 0-100 dB
        
        return {
            "temperatura": round(temperature, 2),
            "humedad": round(humidity, 2),
            "luz": round(light, 2),
            "ruido": round(noise, 2)
        }
        
    except Exception as e:
        print(f"Error leyendo sensores: {e}")
        return None

def publish_sensor_data():
    """Publica datos de sensores via MQTT"""
    if not mqtt_client or not connected:
        return
        
    sensor_data = read_sensors()
    if not sensor_data:
        return
    
    timestamp = time.time()
    
    for sensor_name, value in sensor_data.items():
        try:
            message = {
                "sensor": sensor_name,
                "value": value,
                "unit": get_sensor_unit(sensor_name),
                "timestamp": timestamp,
                "device_id": CLIENT_ID
            }
            
            topic = f"proyecto/sensores/{sensor_name}"
            mqtt_client.publish(topic, ujson.dumps(message))
            
        except Exception as e:
            print(f"Error publicando {sensor_name}: {e}")

def get_sensor_unit(sensor_name):
    """Retorna la unidad de medida para cada sensor"""
    units = {
        "temperatura": "°C",
        "humedad": "%",
        "luz": "lux",
        "ruido": "dB"
    }
    return units.get(sensor_name, "")

def control_fan(message):
    """Controla el ventilador"""
    try:
        action = message.get("action", "off")
        intensity = message.get("intensity", 0)
        
        if action == "on" and 0 <= intensity <= 100:
            duty = int((intensity / 100) * 1023)  # PWM duty cycle
            FAN_PIN.duty(duty)
            print(f"Ventilador encendido al {intensity}%")
        else:
            FAN_PIN.duty(0)
            print("Ventilador apagado")
            
    except Exception as e:
        print(f"Error controlando ventilador: {e}")

def control_led_actuator(message):
    """Controla el LED actuador"""
    try:
        action = message.get("action", "off")
        intensity = message.get("intensity", 0)
        
        if action == "on" and 0 <= intensity <= 100:
            duty = int((intensity / 100) * 1023)
            LED_ACTUATOR.duty(duty)
            print(f"LED encendido al {intensity}%")
        else:
            LED_ACTUATOR.duty(0)
            print("LED apagado")
            
    except Exception as e:
        print(f"Error controlando LED: {e}")

def control_pump(message):
    """Controla la bomba"""
    try:
        action = message.get("action", "off")
        intensity = message.get("intensity", 0)
        
        if action == "on" and 0 <= intensity <= 100:
            duty = int((intensity / 100) * 1023)
            PUMP_PIN.duty(duty)
            print(f"Bomba encendida al {intensity}%")
        else:
            PUMP_PIN.duty(0)
            print("Bomba apagada")
            
    except Exception as e:
        print(f"Error controlando bomba: {e}")

def emergency_stop():
    """Detiene todos los actuadores inmediatamente"""
    print("PARADA DE EMERGENCIA ACTIVADA")
    FAN_PIN.duty(0)
    LED_ACTUATOR.duty(0)
    PUMP_PIN.duty(0)
    
    # Enviar confirmación
    if mqtt_client:
        msg = {
            "device_id": CLIENT_ID,
            "status": "emergency_stop_executed",
            "timestamp": time.time()
        }
        mqtt_client.publish("proyecto/estado/esp32/emergencia", 
                          ujson.dumps(msg))

def main_loop():
    """Bucle principal del programa"""
    global last_sensor_reading
    
    while True:
        try:
            # Verificar mensajes MQTT
            if mqtt_client:
                mqtt_client.check_msg()
            
            # Publicar datos de sensores cada 5 segundos
            current_time = time.time()
            if current_time - last_sensor_reading >= 5:
                publish_sensor_data()
                last_sensor_reading = current_time
            
            # Limpiar memoria
            if current_time % 30 == 0:
                gc.collect()
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error en bucle principal: {e}")
            time.sleep(1)

def main():
    """Función principal"""
    print("Iniciando ESP32 - Agente IA")
    
    # Configurar PWM para actuadores
    FAN_PIN.freq(1000)
    LED_ACTUATOR.freq(1000)
    PUMP_PIN.freq(1000)
    
    # Conectar WiFi
    if not connect_wifi():
        print("Error crítico: No se pudo conectar a WiFi")
        return
    
    time.sleep(2)
    
    # Conectar MQTT
    if not connect_mqtt():
        print("Error crítico: No se pudo conectar a MQTT")
        return
    
    print("Sistema inicializado correctamente")
    
    # Ejecutar bucle principal
    try:
        main_loop()
    except KeyboardInterrupt:
        print("Programa detenido por usuario")
    except Exception as e:
        print(f"Error crítico: {e}")
    finally:
        # Cleanup
        emergency_stop()
        if mqtt_client:
            mqtt_client.disconnect()
        print("Sistema detenido")

if __name__ == "__main__":
    main()