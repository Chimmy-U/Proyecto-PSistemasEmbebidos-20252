"""
Cliente MQTT para Raspberry Pi
Maneja la comunicación bidireccional con ESP32
"""

import json
import time
import logging
from typing import Callable, Dict, Any
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class MQTTManager:
    """Gestor de conexión MQTT"""
    
    def __init__(self, sensor_callback: Callable):
        self.broker_host = "localhost"
        self.broker_port = 1883
        self.client_id = "RPI_MAIN"
        self.client = None
        self.connected = False
        self.sensor_callback = sensor_callback
        
        # Tópicos de suscripción
        self.subscribe_topics = [
            "proyecto/sensores/+",
            "proyecto/estado/esp32/+"
        ]
    
    def start(self):
        """Inicia la conexión MQTT"""
        try:
            self.client = mqtt.Client(self.client_id)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            logger.info(f"Conectando a broker MQTT en {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Esperar conexión
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            if self.connected:
                logger.info("Cliente MQTT iniciado correctamente")
                return True
            else:
                logger.error("Timeout conectando MQTT")
                return False
                
        except Exception as e:
            logger.error(f"Error iniciando MQTT: {e}")
            return False
    
    def stop(self):
        """Detiene la conexión MQTT"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Cliente MQTT detenido")
    
    def publish(self, topic: str, data: Dict[str, Any], qos: int = 1):
        """Publica un mensaje MQTT"""
        try:
            if not self.connected:
                logger.warning("MQTT no conectado, no se puede publicar")
                return False
            
            message = json.dumps(data)
            result = self.client.publish(topic, message, qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Mensaje publicado en {topic}")
                return True
            else:
                logger.error(f"Error publicando en {topic}: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publicando mensaje: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback de conexión MQTT"""
        if rc == 0:
            self.connected = True
            logger.info("Conectado al broker MQTT")
            
            # Suscribirse a tópicos
            for topic in self.subscribe_topics:
                client.subscribe(topic, qos=1)
                logger.info(f"Suscrito a: {topic}")
                
            # Publicar estado de conexión
            status_data = {
                "device_id": self.client_id,
                "status": "connected",
                "timestamp": time.time()
            }
            self.publish("proyecto/estado/rpi/conectado", status_data, qos=2)
            
        else:
            self.connected = False
            logger.error(f"Error conectando MQTT: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback de desconexión MQTT"""
        self.connected = False
        if rc != 0:
            logger.warning("Desconexión inesperada del broker MQTT")
        else:
            logger.info("Desconectado del broker MQTT")
    
    def _on_message(self, client, userdata, msg):
        """Callback de mensaje recibido"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            
            logger.debug(f"Mensaje recibido de {topic}: {data}")
            
            # Procesar según el tipo de mensaje
            if "sensores" in topic:
                self.sensor_callback(topic, data)
            elif "estado/esp32" in topic:
                self._handle_esp32_status(topic, data)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje MQTT: {e}")
    
    def _handle_esp32_status(self, topic: str, data: Dict[str, Any]):
        """Maneja mensajes de estado del ESP32"""
        try:
            device_id = data.get('device_id', 'unknown')
            status = data.get('status', 'unknown')
            
            if "conectado" in topic:
                logger.info(f"ESP32 {device_id} conectado")
            elif "emergencia" in topic:
                logger.critical(f"ESP32 {device_id}: {status}")
                
        except Exception as e:
            logger.error(f"Error procesando estado ESP32: {e}")